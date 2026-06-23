import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const STORAGE_FILE = path.join(__dirname, '../data/bookings.json');

// Ensure data directory exists
const ensureDataDir = () => {
  const dataDir = path.join(__dirname, '../data');
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
};

// Load all bookings from file
export const loadBookings = () => {
  try {
    ensureDataDir();
    if (fs.existsSync(STORAGE_FILE)) {
      const data = fs.readFileSync(STORAGE_FILE, 'utf8');
      const bookings = JSON.parse(data);
      return new Map(Object.entries(bookings));
    }
  } catch (error) {
    console.error('Error loading bookings:', error);
  }
  return new Map();
};

// Save all bookings to file
export const saveBookings = (bookingsMap) => {
  try {
    ensureDataDir();
    const bookingsObj = Object.fromEntries(bookingsMap);
    fs.writeFileSync(STORAGE_FILE, JSON.stringify(bookingsObj, null, 2));
    console.log('💾 Saved to file:', STORAGE_FILE);
    console.log('📊 Total bookings:', bookingsMap.size);
  } catch (error) {
    console.error('❌ Error saving bookings:', error);
  }
};

// Get a single booking
export const getBooking = (token) => {
  const bookings = loadBookings();
  console.log('🔍 Looking for token in storage. Total bookings:', bookings.size);
  console.log('🔍 Available tokens:', Array.from(bookings.keys()));
  return bookings.get(token);
};

// Save a single booking
export const saveBooking = (token, bookingData) => {
  const bookings = loadBookings();
  bookings.set(token, bookingData);
  saveBookings(bookings);
};

// Delete a booking
export const deleteBooking = (token) => {
  const bookings = loadBookings();
  bookings.delete(token);
  saveBookings(bookings);
};

// Initialize storage on startup
export const initializeStorage = () => {
  ensureDataDir();
  console.log('📁 Persistent storage initialized');
};
