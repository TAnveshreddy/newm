Shopkeeper — deploy bundle
==========================
This folder is the deploy-ready site (cloud mode, Firebase configured).

Deploy:
  • Netlify Drop: drag this whole "dist" folder (or shopkeeper-dist.zip)
    onto https://app.netlify.com/drop
  • Or any static host: serve index.html at the site root.

index.html is fully self-contained (HTML+CSS+JS inlined; Firebase from CDN).
Nothing to build, no node_modules, no environment variables.

Firebase console still needs (one-time):
  1. Firestore -> Rules -> publish firestore.rules
  2. Authentication -> enable Google + Phone
  3. Authentication -> Settings -> Authorized domains -> add your site domain
  4. After first login: Firestore users/<uid> -> set role = admin
