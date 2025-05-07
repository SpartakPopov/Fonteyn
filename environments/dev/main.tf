provider "azurerm" {
    features {}
    subscription_id = var.subscription_id
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

module "VNet_One" {
  source = "../../modules/network"
  prefix = var.prefix
  address_space = var.address_space
  location = var.location
  resource_group_name = var.resource_group_name
  subnets = var.subnets

  tags = var.tags
}
