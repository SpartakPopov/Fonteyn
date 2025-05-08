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
resource "azurerm_resource_group" "rg-dev" {
  name     = var.resource_group_name
  location = var.location

  tags = var.tags
}

#VNet + Subnets
resource "azurerm_virtual_network" "vnet_spoke_dev" {
  name                = "${var.prefix}-vnet"
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.address_space

  tags = var.tags
}

resource "azurerm_subnet" "app" {
  name                 = "app"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet_spoke_dev.name
  address_prefixes     = ["10.10.1.0/24"]
}

resource "azurerm_subnet" "db" {
  name                 = "db"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet_spoke_dev.name
  address_prefixes     = ["10.10.2.0/24"]
}

resource "azurerm_subnet" "sensor" {
  name                 = "sensor"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet_spoke_dev.name
  address_prefixes     = ["10.10.3.0/24"]
}


#Hub Peering
resource "azurerm_virtual_network_peering" "dev_to_hub" {
  name                      = "dev-to-hub"
  resource_group_name       = var.resource_group_name
  virtual_network_name      = azurerm_virtual_network.vnet_spoke_dev.name
  remote_virtual_network_id = data.terraform_remote_state.core.outputs.hub_vnet_id

  allow_forwarded_traffic = true
  allow_gateway_transit   = false
}
