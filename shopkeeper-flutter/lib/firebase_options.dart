// Firebase configuration for the shopkeeper-poc project (same project/schema as
// the web apps). These are PUBLIC client identifiers — access is controlled by
// the Firestore security rules, not by hiding these values.
//
// For a production device build, run `flutterfire configure` to generate proper
// per-platform options (and android/app/google-services.json). The values below
// are the project's web app config, sufficient to get started.
import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) return web;
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      default:
        return web;
    }
  }

  static const FirebaseOptions web = FirebaseOptions(
    apiKey: 'AIzaSyChSPt9U-4vSBvecTdre7E6XJI7ypi2Qlk',
    appId: '1:762784521075:web:d774907da55cb978e24306',
    messagingSenderId: '762784521075',
    projectId: 'shopkeeper-poc',
    authDomain: 'shopkeeper-poc.firebaseapp.com',
    storageBucket: 'shopkeeper-poc.firebasestorage.app',
  );

  // Android/iOS reuse the project config; replace via `flutterfire configure`
  // with platform-specific appIds + google-services.json / GoogleService-Info.
  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyChSPt9U-4vSBvecTdre7E6XJI7ypi2Qlk',
    appId: '1:762784521075:web:d774907da55cb978e24306',
    messagingSenderId: '762784521075',
    projectId: 'shopkeeper-poc',
    storageBucket: 'shopkeeper-poc.firebasestorage.app',
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'AIzaSyChSPt9U-4vSBvecTdre7E6XJI7ypi2Qlk',
    appId: '1:762784521075:web:d774907da55cb978e24306',
    messagingSenderId: '762784521075',
    projectId: 'shopkeeper-poc',
    storageBucket: 'shopkeeper-poc.firebasestorage.app',
    iosBundleId: 'com.shopkeeper.shopkeeperMobile',
  );
}
