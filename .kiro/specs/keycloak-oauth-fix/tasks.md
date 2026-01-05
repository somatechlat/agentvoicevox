# Implementation Plan: Keycloak OAuth and Infrastructure Fix

## Overview

This implementation plan fixes the Keycloak OAuth scope configuration and Temporal workflow infrastructure issues.

## Tasks

- [x] 1. Fix Keycloak realm client scopes
  - [x] 1.1 Add missing OIDC client scopes to realm JSON
    - Add `openid` scope with sub mapper
    - Add `profile` scope with name, given_name, family_name, preferred_username mappers
    - Add `email` scope with email, email_verified mappers
    - Keep existing `roles` scope
    - _Requirements: 1.1-1.5_

  - [x] 1.2 Update client default scopes
    - Ensure `agentvoicebox-portal` has all four scopes
    - Ensure `agentvoicebox-api` has all four scopes
    - _Requirements: 1.6, 1.7_

- [x] 2. Verify Google Identity Provider configuration
  - [x] 2.1 Confirm Google IdP settings
    - Verify client ID and secret are correct
    - Verify default scope is `openid profile email`
    - Verify redirect URIs are correct
    - _Requirements: 2.1-2.6_

- [x] 3. Fix Temporal worker configuration
  - [x] 3.1 Update Temporal worker to use correct namespace
    - Ensure namespace is `agentvoicebox`
    - Ensure task queue is `default`
    - _Requirements: 4.1, 4.2_

  - [x] 3.2 Verify workflow and activity registration
    - Check all workflows are registered
    - Check all activities are registered
    - _Requirements: 4.3, 4.4, 4.5_

- [x] 4. Restart services and verify
  - [x] 4.1 Restart Keycloak with updated realm
    - Export updated realm JSON
    - Restart Keycloak container
    - Verify scopes are available
    - _Requirements: 1.1-1.7_

  - [x] 4.2 Restart Temporal worker
    - Restart worker container
    - Verify workflows are registered
    - _Requirements: 4.3-4.6_

- [x] 5. Test authentication flows
  - [x] 5.1 Test Keycloak direct login
    - Verify OAuth flow works with all scopes
    - Verify token contains expected claims
    - _Requirements: 3.1-3.6_

  - [x] 5.2 Test Google OAuth login
    - Verify Google IdP flow works
    - Verify user is created/linked in Keycloak
    - _Requirements: 2.1-2.6_

## Notes

- The main issue is missing standard OIDC client scopes in Keycloak
- Keycloak 24+ requires explicit scope definitions
- Temporal namespace must exist before worker can connect

