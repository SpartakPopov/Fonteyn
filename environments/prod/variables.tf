variable "resource_group_name" {
  description = "Azure RG Name"
  default = "rg-fonteyn-prod"
}

variable "subscription_id" {
  description = "Azure Subscription ID"
  type = string
}

variable "location" {
  description = "Azure region where the resources will be deployed"
  default     = "northeurope"
}

variable "prefix" {
  description = "Prefix for naming resources"
  default     = "prod"
}

variable "address_space" {
  description = "CIDR block for the VNet"
  default     = ["10.20.0.0/16"]
}

variable "subnets" {
  description = "List of subnets for the Dev VNet"
  default = [
    {
      name           = "prod"
      address_prefix = "10.20.1.0/24"
    }
  ]
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default = {
    Environment = "Production"
    Owner       = "t.duicu@student.fontys.nl"
    Project     = "Fonteyn Cloud Infrastructure"
  }
}
