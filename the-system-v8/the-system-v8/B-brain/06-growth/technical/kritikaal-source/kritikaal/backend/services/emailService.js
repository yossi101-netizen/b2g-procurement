import { Resend } from "resend";
import dotenv from "dotenv";
dotenv.config();

const resend = new Resend(process.env.RESEND_API_KEY);

export const sendEmail = async ({ to, subject, html, cc, bcc, from }) => {
  try {
    const { data, error } = await resend.emails.send({
      from: from || "contact@kritikaal.com",
      to,
      subject,
      html,
      ...(cc && { cc }),
      ...(bcc && { bcc })
    });

    if (error) {
      console.error("Resend API error:", error);
      throw new Error(error.message);
    }

    return data;
  } catch (error) {
    console.error("Error sending email:", error);
    throw error;
  }
};
