variable "prefix" {}
variable "location" {}
variable "resource_group_name" {}
variable "address_space" {
  type = list(string)
}
variable "subnets" {
  description = "List of subnet maps with name and address_prefixes"
  type = list(object({
    name           = string
    address_prefix = string
  }))
}
variable "tags" {
  type = map(string)
}
