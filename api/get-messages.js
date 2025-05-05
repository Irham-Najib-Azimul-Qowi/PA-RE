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

async function getMessages(req, res) {
  let db;
  try {
    // Koneksi ke database
    db = await connectToDatabase();
    const collection = db.collection("messages");

    // Mengambil data dengan pengurutan berdasarkan waktu terbaru
    const messages = await collection
      .find({})
      .sort({ createdAt: -1, savedAt: -1 })
      .toArray();

    console.log(`Retrieved ${messages.length} messages from database`);

    res.status(200).json({
      status: "success",
      data: messages,
      count: messages.length,
      message: "Data berhasil diambil",
    });
  } catch (error) {
    console.error("Error fetching messages:", error);
    res.status(500).json({
      status: "error",
      message: "Gagal mengambil data dari database: " + error.message,
    });
  }
}

module.exports = getMessages;
