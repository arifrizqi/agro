const express = require('express');
const firebaseAdmin = require('firebase-admin');

const router = express.Router();

// Inisialisasi Firebase menggunakan credential yang diberikan
const serviceAccount = require('../serviceaccountkey.json');
firebaseAdmin.initializeApp({
  credential: firebaseAdmin.credential.cert(serviceAccount),
  databaseURL: 'https://agro-vision-403510.firebaseio.com' // URL database Firebase Anda
});

// Handler untuk userHistoryRequest
const userHistoryRequest = (req, res) => {
  // Dapatkan data pengguna dan history prediksi dari body request
  const { userId, history } = req.body;

  // Simpan history prediksi ke Firebase Realtime Database
  const db = firebaseAdmin.database();
  const userHistoryRef = db.ref('userHistory');
  userHistoryRef.child(userId).push().set(history);

  res.status(200).json({ message: 'User history saved successfully' });
};

// Export userHistoryRequest sebagai fungsi handler yang akan dipanggil dari routes.js
module.exports = { userHistoryRequest, router };
