# Firestore Index Deployment Guide

## Overview

This guide explains how to deploy Firestore indexes for optimal query performance.

## Prerequisites

1. Firebase CLI installed:
```bash
npm install -g firebase-tools
```

2. Logged into Firebase:
```bash
firebase login
```

## Index Configuration

The `firestore.indexes.json` file contains all required composite indexes for the application.

## Deployment

### Deploy Indexes

```bash
firebase deploy --only firestore:indexes
```

### Verify Deployment

1. Go to Firebase Console: https://console.firebase.google.com
2. Select your project
3. Navigate to Firestore Database → Indexes
4. Verify all indexes are listed and their status is "Enabled"

## Testing Queries

After deploying indexes, test your queries:

```python
# Test public missions query
missions = mission_service.get_public_missions(limit=10)

# Test creator missions query
missions = mission_service.get_missions_by_creator("user_id")

# Test filtered creator query
missions = mission_service.get_missions_by_creator_and_visibility(
    "user_id", 
    is_public=True
)

# Test enrollment queries
enrollments = enrollment_service.get_enrollments_by_user("user_id")
```

## Updating Indexes

When adding new queries:

1. Add the required index to `firestore.indexes.json`
2. Deploy: `firebase deploy --only firestore:indexes`
3. Wait for build to complete
4. Test the new query

## Security Rules

To deploy security rules:

```bash
firebase deploy --only firestore:rules
```

---

For more information, see:
- [Firestore Index Documentation](https://firebase.google.com/docs/firestore/query-data/indexing)
- [Firebase CLI Reference](https://firebase.google.com/docs/cli)
