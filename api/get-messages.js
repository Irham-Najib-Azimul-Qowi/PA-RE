const { MongoClient } = require("mongodb");

const uri = process.env.MONGODB_URI;
let client = null;
let database = null;

async function connectToDatabase() {
  if (!client) {
    client = new MongoClient(uri);
    await client.connect();
    database = client.db("absensi");
  }
  return database;
}

async function getMessages(req, res) {
  try {
    const db = await connectToDatabase();
    const collection = db.collection("messages");

    // Mengambil data dengan pengurutan berdasarkan waktu terbaru
    const messages = await collection.find({}).sort({ savedAt: -1 }).toArray();

    res.status(200).json({
      status: "success",
      data: messages,
      count: messages.length,
    });
  } catch (error) {
    console.error("Error fetching messages:", error);
    res.status(500).json({
      status: "error",
      message: "Gagal mengambil data dari database",
    });
  }
}

module.exports = getMessages;
