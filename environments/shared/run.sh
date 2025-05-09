#!/bin/bash

# Usage: ./run.sh dev or ./run.sh prod

ENV=$1

if [[ -z "$ENV" ]]; then
  echo "Usage: ./run.sh <env> (dev or prod)"
  exit 1
fi

BACKEND_PATH="./$ENV/backend.tf"
VARS_FILE="./$ENV/$ENV.tfvars"

if [[ ! -f "$BACKEND_PATH" ]]; then
  echo "Error: $BACKEND_PATH does not exist"
  exit 1
fi

if [[ ! -f "$VARS_FILE" ]]; then
  echo "Error: $VARS_FILE does not exist"
  exit 1
fi

echo "Switching to environment: $ENV"

# Copy the backend configuration into current working directory
cp "$BACKEND_PATH" backend.tf

# Initialize Terraform with the selected backend
terraform init

# Apply the configuration with the selected variables
terraform apply -var-file="$VARS_FILE"
