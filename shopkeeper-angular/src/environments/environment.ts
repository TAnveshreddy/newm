/**
 * Development environment.
 * The Firebase web config values are public client identifiers (safe to ship);
 * access is enforced by Firestore security rules, not by hiding these keys.
 * This points at the SAME `shopkeeper-poc` project and schema as the existing app.
 */
export const environment = {
  production: false,
  firebase: {
    apiKey: 'AIzaSyChSPt9U-4vSBvecTdre7E6XJI7ypi2Qlk',
    authDomain: 'shopkeeper-poc.firebaseapp.com',
    projectId: 'shopkeeper-poc',
    storageBucket: 'shopkeeper-poc.firebasestorage.app',
    messagingSenderId: '762784521075',
    appId: '1:762784521075:web:d774907da55cb978e24306',
  },
};
