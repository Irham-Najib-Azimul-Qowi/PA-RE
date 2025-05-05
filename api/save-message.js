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

async function saveMessage(req, res) {
  try {
    const db = await connectToDatabase();
    const collection = db.collection("messages");
    const data = req.body;

    // Validasi data yang diperlukan
    if (!data.name || !data.timestamp || !data.status) {
      return res.status(400).json({
        status: "error",
        message: "Data tidak lengkap. Diperlukan: name, timestamp, dan status",
      });
    }

    const result = await collection.insertOne({
      ...data,
      savedAt: new Date(),
      lastUpdated: new Date(),
    });

    res.status(200).json({
      status: "success",
      data: result,
      message: "Data berhasil disimpan",
    });
  } catch (error) {
    console.error("Error saving message:", error);
    res.status(500).json({
      status: "error",
      message: "Gagal menyimpan data ke database",
    });
  }
}

module.exports = saveMessage;
