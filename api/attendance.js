import clientPromise from "../lib/mongodb";

export default async function handler(req, res) {
  if (req.method !== "POST" && req.method !== "GET") {
    return res.status(405).json({ message: "Method tidak diizinkan" });
  }

  try {
    const client = await clientPromise;
    const db = client.db("absensi_db");
    const collection = db.collection("attendance");

    if (req.method === "POST") {
      const { studentId, courseId, status } = req.body;

      if (!studentId || !courseId || !status) {
        return res.status(400).json({ message: "Data tidak lengkap" });
      }

      const result = await collection.insertOne({
        studentId,
        courseId,
        status,
        timestamp: new Date(),
      });

      return res.status(201).json(result);
    }

    // GET method
    const attendanceData = await collection.find({}).toArray();
    return res.status(200).json(attendanceData);
  } catch (error) {
    console.error("Database Error:", error);
    return res.status(500).json({ message: "Terjadi kesalahan server" });
  }
}
