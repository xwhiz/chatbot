"use client";

import axios from "axios";
import { FormEvent } from "react";
import { toast } from "react-toastify";
import { useRouter } from "next/navigation";
import { useActiveChat } from "@/stores/activeChat";
import { useActiveChatID } from "@/stores/activeChatID";
import useAuth from "@/hooks/useAuth";
import Link from "next/link";

export default function Form() {
  const router = useRouter();
  const { setActiveChat } = useActiveChat();
  const { setActiveChatId } = useActiveChatID();
  const [token, session] = useAuth();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const form = event.target as HTMLFormElement;
    const formData = new FormData(form);

    // validate data
    const userName = formData.get("userName") as string;
    const userEmail = formData.get("userEmail") as string;
    const userPassword = formData.get("userPassword") as string;
    const confirmPassword = formData.get("confirmPassword") as string;

    if (userPassword !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    if (!userName || !userEmail || !userPassword) {
      toast.error("Please fill all fields");
      return;
    }
    if (
      userName.length === 0 ||
      userEmail.length === 0 ||
      userPassword.length === 0
    ) {
      toast.error("Please fill all fields");
      return;
    }
    if (userPassword.length < 8) {
      toast.error("Password must be at least 8 characters long");
      return;
    }

    try {
      const response = await axios.post(
        process.env.NEXT_PUBLIC_API_URL + "/auth/register",
        {
          name: userName,
          email: userEmail,
          password: userPassword,
          role: "user",
        }
      );
      const data = response.data;
      toast.success(data.message);
      form.reset();

      const token = data.data.access_token;

      window.localStorage.setItem("token", token);

      setActiveChatId("");
      setActiveChat({
        id: "",
        title: "",
        user_email: "",
        messages: [],
      });

      router.push("/");
    } catch (error) {
      const data = (error as any).response.data;

      if (!data.success) {
        toast.error(data.message);
        return;
      }

      toast.error("An error occurred. Please try again.");
    }
  }

  return (
    <>
      {token ? (
        <div className="text-center mt-6">
          <Link
            href="/profile"
            className="text-slate-800 text-sm font-bold leading-relaxed inline-block py-2 whitespace-nowrap uppercase underline cursor-pointer"
          >
            Go to your profile
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="relative w-full mb-3">
            <label
              className="block uppercase text-blueGray-600 text-xs font-bold mb-2"
              htmlFor="userName"
            >
              Name
            </label>
            <input
              type="text"
              id="userName"
              name="userName"
              className="border-0 px-3 py-3 placeholder-blueGray-300 text-blueGray-600 bg-white rounded text-sm shadow focus:outline-none focus:ring w-full ease-linear transition-all duration-150"
              placeholder="e.g. John Doe"
              required
            />
          </div>

          <div className="relative w-full mb-3">
            <label
              className="block uppercase text-blueGray-600 text-xs font-bold mb-2"
              htmlFor="userEmail"
            >
              Email
            </label>
            <input
              type="email"
              id="userEmail"
              name="userEmail"
              className="border-0 px-3 py-3 placeholder-blueGray-300 text-blueGray-600 bg-white rounded text-sm shadow focus:outline-none focus:ring w-full ease-linear transition-all duration-150"
              placeholder="e.g. john.doe@gmail.com"
              required
            />
          </div>

          <div className="relative w-full mb-3">
            <label
              className="block uppercase text-blueGray-600 text-xs font-bold mb-2"
              htmlFor="userPassword"
            >
              Password
            </label>
            <input
              type="password"
              id="userPassword"
              name="userPassword"
              className="border-0 px-3 py-3 placeholder-blueGray-300 text-blueGray-600 bg-white rounded text-sm shadow focus:outline-none focus:ring w-full ease-linear transition-all duration-150"
              placeholder="Password"
              required
            />
          </div>

          <div className="relative w-full mb-3">
            <label
              className="block uppercase text-blueGray-600 text-xs font-bold mb-2"
              htmlFor="confirmPassword"
            >
              Confirm Password
            </label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              className="border-0 px-3 py-3 placeholder-blueGray-300 text-blueGray-600 bg-white rounded text-sm shadow focus:outline-none focus:ring w-full ease-linear transition-all duration-150"
              placeholder="Password"
              required
            />
          </div>

          <div className="text-center mt-6">
            <button
              className="bg-slate-800 text-white active:bg-slate-600 text-sm font-bold uppercase px-6 py-3 rounded shadow hover:shadow-lg outline-none focus:outline-none mr-1 mb-1 w-full ease-linear transition-all duration-150"
              type="submit"
            >
              Create Account
            </button>
          </div>

          <div className="text-center mt-6">
            Already have an account?{" "}
            <a
              href="/login"
              className="text-slate-800 text-sm font-bold leading-relaxed inline-block py-2 whitespace-nowrap uppercase underline cursor-pointer"
            >
              Login
            </a>
          </div>
        </form>
      )}
    </>
  );
}
