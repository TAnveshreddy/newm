# Shopkeeper — Firebase setup

This build adds Firebase Authentication (Google + Mobile OTP) and per-record
Firestore sync to the single-file `shopkeeper.html` app, so the same account
sees the same data on desktop and mobile.

Until you fill in the config, the app runs in **local-only mode** and behaves
exactly like before (all data in the browser, no cloud).

## 1. Paste your Firebase config

In `shopkeeper.html`, find `window.firebaseConfig` (near the top) and replace
the `PASTE_*` placeholders with your project's web-app config from:

**Firebase Console → Project Settings (gear) → Your apps → Web app → SDK setup and configuration.**

```js
window.firebaseConfig = {
  apiKey:            "AIza...",
  authDomain:        "shopkeeper-poc.firebaseapp.com",
  projectId:         "shopkeeper-poc",
  storageBucket:     "shopkeeper-poc.appspot.com",
  messagingSenderId: "...",
  appId:             "1:...:web:..."
};
```

(The `apiKey` is a public client identifier, not a secret — it is safe to ship
in the HTML. Access is controlled by the Firestore rules, not by hiding the key.)

## 2. Enable sign-in methods (one time, in the console)

- **Authentication → Sign-in method → Google** → enable.
- **Authentication → Sign-in method → Phone** → enable.
  - Phone OTP uses Firebase's built-in SMS via an invisible reCAPTCHA — **no
    backend or Twilio needed**. For local testing you can add test numbers
    under Phone → *Phone numbers for testing*.
- **Authentication → Settings → Authorized domains** → add the domain you serve
  the file from. `localhost` is allowed by default. (Opening the file directly
  as `file://` will **not** work for auth — serve it over http, e.g.
  `python3 -m http.server`.)

## 3. Create Firestore and deploy the rules

- **Firestore Database → Create database** (production mode).
- **Firestore Database → Rules** → paste the contents of `firestore.rules` → Publish.

## 4. Make yourself admin

There is no admin until you create one:

- **Option A (recommended):** log in once (Google or OTP). Then in Firestore open
  `users/<your-uid>` and set field **`role` = `admin`**.
- **Option B (bootstrap):** before first login, add your number/email to
  `window.ADMIN_BOOTSTRAP` in `shopkeeper.html`, e.g.
  `{ phones: ['9876543210'], emails: ['you@gmail.com'] }`. The first matching
  login is created as admin automatically. Clear the list afterwards.

## Data model

```
users/{uid}                      profile: phone, email, plan, role, active,
                                 createdAt, activatedAt, lastLogin
userData/{uid}/parties/{id}      one doc per customer / supplier
userData/{uid}/items/{id}        one doc per product / service
userData/{uid}/txns/{id}         one doc per transaction
userData/{uid}/adjustments/{id}  one doc per stock adjustment
userData/{uid}/meta/settings     business settings (single doc)
userData/{uid}/meta/counters     invoice-number counters (single doc)
```

## How the sync works

- On login, if the account's cloud is empty, this device's current data is
  pushed up as the starting point; otherwise the cloud copy is authoritative
  and loads into the app.
- Every local change (`save()`) is pushed to Firestore as individual record
  writes (debounced ~0.7s), so two devices merge at the record level instead of
  overwriting each other's whole dataset.
- Real-time `onSnapshot` listeners apply remote changes to the open app, so a
  bill made on the desktop appears on the mobile within moments (and vice-versa).
- Firestore offline persistence is enabled: the app keeps working with no
  internet and syncs automatically when the connection returns.
- The 🔄 **Sync** button forces an immediate push.

## Not in this pass

Admin dashboard UI (list users, activate/deactivate, change plans/roles) and
subscription enforcement are the planned next step. The data model and rules
above already support them — an admin can manage `users/*` today directly in
the Firestore console.

## Testing checklist

1. Serve over http (`python3 -m http.server 8080`) and open `localhost:8080/shopkeeper.html`.
2. Log in with Google, add a customer and a bill.
3. Open the same URL in another browser/device, log in with the **same** account
   → the customer and bill appear automatically.
4. Change something on device B → it appears on device A.
5. Go offline, add a bill, come back online → it syncs up.
