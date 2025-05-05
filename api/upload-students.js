const { MongoClient } = require("mongodb");
const XLSX = require("xlsx");
const express = require("express");
const router = express.Router();
const fileUpload = require("express-fileupload");

router.use(fileUpload());

const uri = process.env.MONGODB_URI;
const client = new MongoClient(uri);

async function connectDB() {
  await client.connect();
  return client.db("absensi");
}

router.post("/", async (req, res) => {
  try {
    if (!req.files || !req.files.excel) {
      return res
        .status(400)
        .json({ status: "error", message: "No file uploaded" });
    }

    const file = req.files.excel;
    const workbook = XLSX.read(file.data, { type: "buffer" });
    const sheet = workbook.Sheets[workbook.SheetNames[0]];
    const data = XLSX.utils.sheet_to_json(sheet);

    // Validasi kolom
    const requiredColumns = ["name", "course"];
    const firstRow = data[0];
    if (!firstRow || !requiredColumns.every((col) => col in firstRow)) {
      return res
        .status(400)
        .json({
          status: "error",
          message: "File XLS harus memiliki kolom 'name' dan 'course'",
        });
    }

    const db = await connectDB();
    const collection = db.collection("students");

    // Hapus data lama (opsional, tergantung kebutuhan)
    await collection.deleteMany({});

    // Simpan data siswa
    const result = await collection.insertMany(
      data.map((row) => ({
        name: row.name,
        course: row.course,
      }))
    );

    res.status(200).json({ status: "success", data: result });
  } catch (error) {
    res.status(500).json({ status: "error", message: error.message });
  } finally {
    await client.close();
  }
});

module.exports = router;
