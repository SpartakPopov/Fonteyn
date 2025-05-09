#Referencing remote data from Core Environment
data "terraform_remote_state" "core" {
  backend = "azurerm"
  config = {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstatefict17"
    container_name       = "tfstate"
    key                  = "core.terraform.tfstate"
  }
}

#Resource Group
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location

  tags = var.tags
}

#VNet + Subnets
resource "azurerm_virtual_network" "vnet_spoke" {
  name                = "${var.prefix}-vnet"
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.address_space

  depends_on = [azurerm_resource_group.rg]

  tags = var.tags
}

resource "azurerm_subnet" "app" {
  name                 = "${var.prefix}-app"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet_spoke.name
  address_prefixes     = [var.subnets[0]["address_prefix"]]
}

resource "azurerm_subnet" "db" {
  name                 = "${var.prefix}-db"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet_spoke.name
  address_prefixes     = [var.subnets[1]["address_prefix"]]
}

resource "azurerm_subnet" "sensor" {
  name                 = "${var.prefix}-sensor"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet_spoke.name
  address_prefixes     = [var.subnets[2]["address_prefix"]]
}


#Hub Peering
resource "azurerm_virtual_network_peering" "hub_peering" {
  name                      = "${var.prefix}-to-hub"
  resource_group_name       = var.resource_group_name
  virtual_network_name      = azurerm_virtual_network.vnet_spoke.name
  remote_virtual_network_id = data.terraform_remote_state.core.outputs.hub_vnet_id

  allow_forwarded_traffic = true
  allow_gateway_transit   = false
}
