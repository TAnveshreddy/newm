# Shopkeeper — Firebase setup

This build adds Firebase Authentication (Google + Mobile OTP) and per-record
Firestore sync to the single-file `index.html` app, so the same account
sees the same data on desktop and mobile.

Until you fill in the config, the app runs in **local-only mode** and behaves
exactly like before (all data in the browser, no cloud).

## 1. Paste your Firebase config

In `index.html`, find `window.firebaseConfig` (near the top) and replace
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
  `window.ADMIN_BOOTSTRAP` in `index.html`, e.g.
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

## Admin console

Once your account's `role` is `admin` (see step 4), an **🛡️ Admin** entry
appears in the sidebar (and a shortcut in Settings → *Account & Subscription*).
It is fully in-app now — no need to edit Firestore by hand:

- **View all registered users** in one table, with a live search box.
- **Active / inactive counts** and per-user status badges at a glance.
- **Activate / deactivate accounts** — deactivating locks the user out on all
  their devices immediately (their open session drops to the "account
  deactivated" screen via a real-time profile listener). Activating stamps a
  fresh *activation date*.
- **Delete accounts** — removes the profile **and** the user's business data
  subtree (parties, items, transactions, settings, counters).
- **Upgrade / downgrade subscription plans** (`free → basic → premium →
  enterprise`) from a dropdown.
- **Manage roles / permissions** (`user` ⇄ `admin`) from a dropdown.
- **See registration, activation and last-login** timestamps per user.
- **Export the user list to CSV**.

Guard-rails: an admin can't deactivate, delete, or demote **their own**
account from the console (prevents locking yourself out), and every action is
still authorised server-side by `firestore.rules` — the UI only exposes what an
admin is already allowed to do.

> **Note on account deletion:** removing the Firebase *Authentication* login
> record itself requires the Admin SDK on a backend (not available from the
> browser). The console deletes the user's Firestore profile and all their
> data, which unlinks them from that data. For a hard auth delete, remove the
> user under **Authentication → Users** in the console, or wire up an Admin-SDK
> Cloud Function.

## Subscription enforcement

Plans are stored and managed today; gating specific features behind a paid
plan is a small follow-up — read `window._fbProfile.plan` wherever you want to
limit a feature. The admin console already sets the plan each user is on.

## Testing checklist

1. Serve over http (`python3 -m http.server 8080`) and open `localhost:8080/index.html`.
2. Log in with Google, add a customer and a bill.
3. Open the same URL in another browser/device, log in with the **same** account
   → the customer and bill appear automatically.
4. Change something on device B → it appears on device A.
5. Go offline, add a bill, come back online → it syncs up.
