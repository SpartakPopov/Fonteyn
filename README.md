# Cloud Infrastructure Terraform Project

This repository contains Terraform configurations for managing cloud infrastructure across multiple environments (core, shared, dev, prod).

## Structure

- `environments/` — Environment-specific configurations
  - `core/` — Core infrastructure
  - `shared/` — Shared resources
    - `dev/` — Development environment
    - `prod/` — Production environment

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) installed
- Access to the target cloud provider (credentials configured)

## How to Redeploy an Environment

1. **Use the provided `run.sh` script with `dev` or `prod` argument:**
   ```sh
   ./run.sh
   ```
   *(You may need to adapt this for Windows or run the commands manually as above.)*

## Notes
- Make sure you have the necessary permissions to create and modify resources in your cloud account.
- Review the `variables.tf` and `terraform.tfvars` files to customize your deployment.
- Outputs will be shown after a successful `terraform apply`.

## Troubleshooting
- If you encounter issues, try running `terraform init` again or check your cloud provider credentials.
- For more details, refer to the Terraform documentation or the comments in each `.tf` file.

---

*This project is intended for educational and demonstration purposes.*
