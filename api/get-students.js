const { MongoClient } = require("mongodb");

const uri = process.env.MONGODB_URI;
const client = new MongoClient(uri);

async function getStudents(req, res) {
  try {
    await client.connect();
    const db = client.db("absensi");
    const studentsCollection = db.collection("students");

    // Ambil semua data siswa
    const students = await studentsCollection.find({}).toArray();

    res.status(200).json(students);
  } catch (error) {
    res.status(500).json({ status: "error", message: error.message });
  } finally {
    await client.close();
  }
}

module.exports = getStudents;
