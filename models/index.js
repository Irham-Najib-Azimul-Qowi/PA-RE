import mongoose from "mongoose";

// Skema Mahasiswa
const studentSchema = new mongoose.Schema({
  name: { type: String, required: true },
  nim: { type: String, required: true, unique: true },
  images: [String],
  createdAt: { type: Date, default: Date.now },
});

// Skema Mata Kuliah
const courseSchema = new mongoose.Schema({
  name: { type: String, required: true },
  date: { type: Date, required: true },
  startTime: { type: String, required: true },
  endTime: { type: String, required: true },
  createdAt: { type: Date, default: Date.now },
});

// Skema Absensi
const attendanceSchema = new mongoose.Schema({
  studentId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "Student",
    required: true,
  },
  courseId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "Course",
    required: true,
  },
  status: { type: String, enum: ["hadir", "tidak hadir"], required: true },
  timestamp: { type: Date, default: Date.now },
});

// Skema Jadwal Perorangan
const individualScheduleSchema = new mongoose.Schema({
  name: { type: String, required: true },
  date: { type: Date, required: true },
  startTime: { type: String, required: true },
  endTime: { type: String, required: true },
  createdAt: { type: Date, default: Date.now },
});

// Skema Log
const logSchema = new mongoose.Schema({
  message: { type: String, required: true },
  type: { type: String, enum: ["info", "warning", "error"], default: "info" },
  timestamp: { type: Date, default: Date.now },
});

// Export model jika belum ada
export const Student =
  mongoose.models.Student || mongoose.model("Student", studentSchema);
export const Course =
  mongoose.models.Course || mongoose.model("Course", courseSchema);
export const Attendance =
  mongoose.models.Attendance || mongoose.model("Attendance", attendanceSchema);
export const IndividualSchedule =
  mongoose.models.IndividualSchedule ||
  mongoose.model("IndividualSchedule", individualScheduleSchema);
export const Log = mongoose.models.Log || mongoose.model("Log", logSchema);
