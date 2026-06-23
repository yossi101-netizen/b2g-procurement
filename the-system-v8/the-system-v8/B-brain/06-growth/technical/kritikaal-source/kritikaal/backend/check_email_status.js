import { Resend } from "resend";
import dotenv from "dotenv";
dotenv.config();

const resend = new Resend(process.env.RESEND_API_KEY);

async function checkEmails() {
  try {
    const adminEmailId = 'ee7872f5-abe9-41db-bd01-4be611ae579f';
    const userEmailId = 'db1a07df-d3c1-484d-8e14-422f66ce7635';

    console.log("Checking Admin Email...");
    const adminRes = await resend.emails.get(adminEmailId);
    console.log(JSON.stringify(adminRes, null, 2));

    console.log("Checking User Email...");
    const userRes = await resend.emails.get(userEmailId);
    console.log(JSON.stringify(userRes, null, 2));
  } catch (error) {
    console.error("Error:", error.message);
  }
}

checkEmails();
