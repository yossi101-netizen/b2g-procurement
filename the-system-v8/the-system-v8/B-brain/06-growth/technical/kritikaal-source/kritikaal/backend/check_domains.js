import { Resend } from "resend";
import dotenv from "dotenv";
dotenv.config();

const resend = new Resend(process.env.RESEND_API_KEY);

async function checkDomains() {
  try {
    const domains = await resend.domains.list();
    console.log("Domains:", JSON.stringify(domains, null, 2));
  } catch (error) {
    console.error("Error checking domains:", error);
  }
}

checkDomains();
