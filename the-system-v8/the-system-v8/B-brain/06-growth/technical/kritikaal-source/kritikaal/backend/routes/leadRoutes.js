import express from "express";
import supabase from "../supabaseClient.js";
import { handleBookCall } from "../controllers/bookingController.js";

const router = express.Router();

router.post("/leads", handleBookCall);

export default router;