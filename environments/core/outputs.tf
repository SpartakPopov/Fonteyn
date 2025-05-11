output "hub_vnet_id" {
  value = azurerm_virtual_network.vnet_hub.id
}

output "hub_vnet_name" {
  value = azurerm_virtual_network.vnet_hub.name
}

output "hub_resource_group" {
  value = azurerm_resource_group.rg-core.name
}

output "log_analytics_id" {
  value = azurerm_log_analytics_workspace.core_logs.id
}

output "backup_storage_id" {
  value = azurerm_storage_account.core_backup.id
}
