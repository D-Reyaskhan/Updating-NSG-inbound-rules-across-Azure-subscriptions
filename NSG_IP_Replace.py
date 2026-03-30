"""
NSG Inbound Rule - IP Range Replacement Across Azure Subscriptions
===================================================================
Replaces OLD_IP_RANGE with NEW_IP_RANGE in NSG inbound rules,
only for rules that actually contain the old IP range.

Requirements:
    pip install azure-identity azure-mgmt-network azure-mgmt-subscription

Auth:
    Uses DefaultAzureCredential — works with:
      - az login (local dev)
      - Managed Identity (Azure VM / pipeline)
      - Service Principal via env vars:
          AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
"""

import logging
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.subscription import SubscriptionClient

# ─────────────────────────────────────────────
# ✏️  CONFIGURE THESE BEFORE RUNNING
# ─────────────────────────────────────────────
OLD_IP_RANGE = "x.x.x.x/32"       # IP range to be replaced
NEW_IP_RANGE = "x.x.x.x/32"       # Replacement IP range
DRY_RUN      = True                # Set False to apply actual changes
TARGET_SUBSCRIPTION_NAME = None    # Set to subscription name to test on one subscription only (None = all)
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


def get_all_subscriptions(credential):
    """Fetch all accessible Azure subscriptions."""
    sub_client = SubscriptionClient(credential)
    subscriptions = [
        sub for sub in sub_client.subscriptions.list()
        if sub.state == "Enabled"
    ]
    log.info(f"Found {len(subscriptions)} enabled subscription(s).")
    return subscriptions


def replace_ip_in_prefix_list(prefixes: list) -> tuple:
    """
    Given a list of address prefixes, replace OLD_IP_RANGE if present.
    Returns (updated_list, was_changed).
    """
    updated = []
    changed = False
    for prefix in prefixes:
        if prefix.strip() == OLD_IP_RANGE:
            updated.append(NEW_IP_RANGE)
            changed = True
        else:
            updated.append(prefix)
    return updated, changed


def process_nsg(network_client, resource_group: str, nsg_name: str, subscription_name: str):
    """Check all inbound rules of an NSG and replace the IP range if found."""
    nsg = network_client.network_security_groups.get(resource_group, nsg_name)
    rules_updated = []
    rules_skipped = []

    for rule in (nsg.security_rules or []):
        # Only process Inbound rules
        if rule.direction.lower() != "inbound":
            continue

        changed = False

        # Handle single source address prefix
        if rule.source_address_prefix and rule.source_address_prefix.strip() == OLD_IP_RANGE:
            if not DRY_RUN:
                rule.source_address_prefix = NEW_IP_RANGE
            rules_updated.append(rule.name)
            changed = True
        # Handle multiple source address prefixes (source_address_prefixes list)
        elif rule.source_address_prefixes:
            new_prefixes, was_changed = replace_ip_in_prefix_list(rule.source_address_prefixes)
            if was_changed:
                if not DRY_RUN:
                    rule.source_address_prefixes = new_prefixes
                rules_updated.append(rule.name)
                changed = True

        if not changed:
            rules_skipped.append(rule.name)

    if rules_updated:
        if not DRY_RUN:
            # Push the updated NSG back to Azure
            network_client.network_security_groups.begin_create_or_update(
                resource_group, nsg_name, nsg
            ).result()
        for rule_name in rules_updated:
            log.info(f"    Rule '{rule_name}': UPDATED")

    for rule_name in rules_skipped:
        log.info(f"    Rule '{rule_name}': SKIPPED")

    return len(rules_updated)


def main():
    log.info("NSG IP Range Replacement Tool")
    log.info(f"OLD IP: {OLD_IP_RANGE} → NEW IP: {NEW_IP_RANGE}")
    log.info("")

    credential = DefaultAzureCredential()
    subscriptions = get_all_subscriptions(credential)

    total_nsgs      = 0
    total_rules_hit = 0

    for sub in subscriptions:
        sub_id   = sub.subscription_id
        sub_name = sub.display_name

        # Skip if filtering to a specific subscription
        if TARGET_SUBSCRIPTION_NAME and sub_name != TARGET_SUBSCRIPTION_NAME:
            continue

        log.info(f"Subscription: {sub_name}")

        network_client = NetworkManagementClient(credential, sub_id)

        try:
            nsgs = list(network_client.network_security_groups.list_all())
        except Exception as e:
            log.warning(f"  ⚠️  Could not list NSGs: {e}")
            continue

        for nsg in nsgs:
            # Extract resource group from NSG's resource ID
            rg_name = nsg.id.split("/")[4]
            log.info(f"  NSG: {nsg.name}")
            total_nsgs += 1

            try:
                rules_changed = process_nsg(network_client, rg_name, nsg.name, sub_name)
                total_rules_hit += rules_changed
            except Exception as e:
                log.error(f"  ❌ Error processing NSG '{nsg.name}': {e}")

        log.info("")

    log.info("Run Complete")
    log.info(f"Total NSGs scanned: {total_nsgs}")
    log.info(f"Total rules updated: {total_rules_hit}")
    log.info(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")


if __name__ == "__main__":
    main()
