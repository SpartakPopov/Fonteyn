output "hub_vnet_id" {
  value = azurerm_virtual_network.vnet_hub.id
}

output "hub_vnet_name" {
  value = azurerm_virtual_network.vnet_hub.name
}

output "hub_resource_group" {
  value = azurerm_resource_group.rg-core.name
}
