const cacheControl = require('express-cache-controller');
const express = require('express');
const routes = require('./routes');
const bodyParser = require('body-parser');
const { initializeApp } = require('firebase/app');
const { getFirestore } = require('firebase/firestore');

const firebaseConfig = {
  // Firebase configuration
  apiKey: "AIzaSyAcS2sMgKIKbIVAwTs229eoQWaFCWxZd9o",
  authDomain: "agro-vision-403510.firebaseapp.com",
  projectId: "agro-vision-403510",
  storageBucket: "agro-vision-403510.appspot.com",
  messagingSenderId: "623850716036",
  appId: "1:623850716036:web:74a7812417e572bb757bd1"
};

const app = express();
const port = 8080;

const firebaseApp = initializeApp(firebaseConfig);
const db = getFirestore(firebaseApp);


app.use(bodyParser.urlencoded({limit: "10mb", extended: true, parameterLimit: 50000}));
app.use(cacheControl({ noCache: true }));
app.use(express.json({limit: "10mb", extended: true}))
app.use(routes);

app.use((req, res, next) => {
  const error = new Error('Not Found');
  error.statusCode = 404;
  next(error);
});

// Error response middleware
app.use((err, req, res, next) => {
  res.status(err.statusCode || 500).json({
    statusCode: err.statusCode || 500,
    error: err.message || 'Not Found',
    message: err.message || 'Not Found'
  });
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});

module.exports = app;