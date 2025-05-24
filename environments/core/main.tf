#Referencing remote data from Dev Environment
data "terraform_remote_state" "dev" {
  backend = "azurerm"
  config = {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstatefict17"
    container_name       = "tfstate"
    key                  = "dev.terraform.tfstate"
  }
}

resource "azurerm_resource_group" "rg-core" {
  name     = var.resource_group_name
  location = var.location

  tags = var.tags
}

#Hub VNet and Subnets
resource "azurerm_virtual_network" "vnet_hub" {
  name                = "${var.prefix}-vnet"
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.address_space

  tags = var.tags
}

resource "azurerm_subnet" "shared_services" {
  name                 = "shared-services"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet_hub.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_subnet" "vpn" {
  name                 = "vpn"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet_hub.name
  address_prefixes     = ["10.0.2.0/24"]
}

#Hub to Dev Peering
resource "azurerm_virtual_network_peering" "hub_to_dev" {
  name                      = "hub-to-dev"
  resource_group_name       = var.resource_group_name
  virtual_network_name      = azurerm_virtual_network.vnet_hub.name
  remote_virtual_network_id = data.terraform_remote_state.dev.outputs.spoke_dev_vnet_id

  allow_forwarded_traffic = true
  allow_gateway_transit   = false
}

#Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "core_logs" {
  name                = "core-log-workspace"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg-core.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = var.tags
}
