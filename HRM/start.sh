#!/bin/env bash
exec uvicorn main:main_app --host 0.0.0.0 --port 443 --log-level debug