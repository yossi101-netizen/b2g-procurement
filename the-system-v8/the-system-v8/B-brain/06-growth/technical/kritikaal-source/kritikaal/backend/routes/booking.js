import express from 'express';
import { handleBookCall } from '../controllers/bookingController.js';

const router = express.Router();

// POST /api/bookings - Create a new booking
router.post('/', handleBookCall);

// POST /api/book-call - Alternative endpoint (same handler)
router.post('/book-call', handleBookCall);

export default router;
