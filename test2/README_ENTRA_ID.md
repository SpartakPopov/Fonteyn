# Entra ID Integration for Fonteyn Holiday Parks

This document explains how to set up and use Microsoft Entra ID (formerly Azure AD) authentication in the Fonteyn Holiday Parks application.

## Prerequisites

1. A Microsoft Entra ID tenant
2. An application registered in Entra ID
3. Python 3.7+ with pip

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=fonteyn_db

# Entra ID Configuration
ENTRA_ID_CLIENT_ID=95697f73-1af0-4b01-8253-e6da816f4f54
ENTRA_ID_CLIENT_SECRET=el68Q~hNuTiwWscLkhDPCNb~y-ntuvrrQThWkdgw
ENTRA_ID_AUTHORITY=https://login.microsoftonline.com/8c28e6dc-ec5c-42dc-9d5f-0be7fa070508
ENTRA_ID_REDIRECT_PATH=/admin/msauth
ENTRA_ID_SCOPE=User.Read

# Flask Configuration
SECRET_KEY=your-secret-key-here
```

### 3. Entra ID Application Configuration

In your Microsoft Entra ID portal:

1. Go to **App registrations** > **New registration**
2. Set the redirect URI to: `https://your-domain.com/admin/msauth`
3. Add the following API permissions:
   - Microsoft Graph > User.Read
4. Generate a client secret and update the `ENTRA_ID_CLIENT_SECRET` in your `.env` file

## Features

### Authentication Methods

The application now supports two authentication methods:

1. **Traditional Login**: Username/password authentication
2. **Entra ID Login**: Microsoft Entra ID authentication

### User Management

- Users can sign in with their Microsoft accounts
- New users are automatically created in the database upon first login
- Existing users are linked to their Microsoft accounts
- Admin privileges can be assigned to Entra ID users

### Security Features

- Secure token handling
- Automatic session management
- CSRF protection
- Secure redirect handling

## Usage

### For Users

1. Navigate to the login page
2. Click "Sign in with Microsoft" button
3. Complete the Microsoft authentication flow
4. You'll be redirected to your dashboard

### For Administrators

1. Sign in with Entra ID
2. Access admin features through the admin dashboard
3. Manage users and reservations
4. Monitor energy consumption

## API Endpoints

### Authentication Endpoints

- `GET /entra-id/login` - Initiate Entra ID authentication
- `GET /admin/msauth` - Handle Entra ID callback
- `GET /entra-id/logout` - Logout from Entra ID

### Protected Endpoints

All existing endpoints now support both authentication methods:
- Dashboard: `/dashboard`
- Booking: `/booking/<type>`
- Reservations: `/make_reservation`
- Energy: `/energy-consumption`

## Troubleshooting

### Common Issues

1. **Redirect URI Mismatch**: Ensure the redirect URI in Entra ID matches your application URL
2. **Invalid Client Secret**: Verify the client secret is correctly set in the `.env` file
3. **Permission Denied**: Check that the required API permissions are granted

### Debug Mode

To enable debug mode, set the following in your `.env` file:

```env
FLASK_ENV=development
FLASK_DEBUG=1
```

## Security Considerations

1. **Client Secret**: Keep your client secret secure and never commit it to version control
2. **HTTPS**: Always use HTTPS in production
3. **Session Management**: Sessions are automatically managed and secured
4. **Token Storage**: Access tokens are not stored in the database

## Support

For issues related to Entra ID integration, please check:
1. Microsoft Entra ID documentation
2. MSAL Python library documentation
3. Application logs for detailed error messages 