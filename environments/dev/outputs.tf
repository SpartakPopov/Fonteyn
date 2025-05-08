output "spoke_dev_vnet_id" {
  value = azurerm_virtual_network.vnet_spoke_dev.id
}

output "spoke_dev_vnet_name" {
  value = azurerm_virtual_network.vnet_spoke_dev.name
}

output "spoke_dev_resource_group" {
  value = azurerm_resource_group.rg-dev.name
}
