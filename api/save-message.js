const { MongoClient } = require("mongodb");

if (!process.env.MONGODB_URI) {
  throw new Error("Please add MongoDB URI to environment variables");
}

const uri = process.env.MONGODB_URI;
const options = {
  useNewUrlParser: true,
  useUnifiedTopology: true,
};

let client = null;
let database = null;

async function connectToDatabase() {
  try {
    if (!client) {
      client = new MongoClient(uri, options);
      await client.connect();
      database = client.db("absensi");
      console.log("Connected to MongoDB");
    }
    return database;
  } catch (error) {
    console.error("MongoDB connection error:", error);
    throw error;
  }
}

async function saveMessage(req, res) {
  let db;
  try {
    // Validasi request body
    const data = req.body;
    if (!data || typeof data !== "object") {
      return res.status(400).json({
        status: "error",
        message: "Invalid request data",
      });
    }

    // Validasi data yang diperlukan
    if (!data.name || !data.timestamp) {
      return res.status(400).json({
        status: "error",
        message: "Data tidak lengkap. Diperlukan: name dan timestamp",
      });
    }

    // Koneksi ke database
    db = await connectToDatabase();
    const collection = db.collection("messages");

    // Persiapkan data untuk disimpan
    const messageData = {
      ...data,
      status: data.status || "Hadir",
      savedAt: new Date(),
      lastUpdated: new Date(),
      createdAt: new Date(),
    };

    // Simpan data
    const result = await collection.insertOne(messageData);

    if (!result.acknowledged) {
      throw new Error("Failed to save data");
    }

    console.log("Data saved successfully:", messageData);

    res.status(201).json({
      status: "success",
      data: messageData,
      message: "Data berhasil disimpan",
    });
  } catch (error) {
    console.error("Error saving message:", error);
    res.status(500).json({
      status: "error",
      message: "Gagal menyimpan data ke database: " + error.message,
    });
  }
}

module.exports = saveMessage;
