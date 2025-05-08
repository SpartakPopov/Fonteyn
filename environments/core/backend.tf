terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstatefict17"
    container_name       = "tfstate"
    key                  = "core.terraform.tfstate"
  }
}
