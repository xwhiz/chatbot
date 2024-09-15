"use client";

import { useActiveChat } from "@/stores/activeChat";
import { useActiveChatID } from "@/stores/activeChatID";
import axios from "axios";
import { useRouter } from "next/navigation";
import { FormEvent } from "react";
import { toast } from "react-toastify";

export default function Form() {
  const router = useRouter();
  const { setActiveChat } = useActiveChat();
  const { setActiveChatId } = useActiveChatID();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const form = event.target as HTMLFormElement;
    const formData = new FormData(form);

    // validate data
    const userEmail = formData.get("userEmail") as string;
    const userPassword = formData.get("userPassword") as string;

    if (!userEmail || !userPassword) {
      toast.error("Please fill in all fields");
      return;
    }

    try {
      const response = await axios.post(
        process.env.NEXT_PUBLIC_API_URL + "/auth/login",
        {
          email: userEmail,
          password: userPassword,
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
    <form onSubmit={handleSubmit}>
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
        />
      </div>

      <div className="text-center mt-6">
        <button
          className="bg-slate-800 text-white active:bg-slate-600 text-sm font-bold uppercase px-6 py-3 rounded shadow hover:shadow-lg outline-none focus:outline-none mr-1 mb-1 w-full ease-linear transition-all duration-150"
          type="submit"
        >
          Login
        </button>
      </div>

      <div className="text-center mt-6">
        Don&apos;t have an account?{" "}
        <a
          href="/register"
          className="text-slate-800 text-sm font-bold leading-relaxed inline-block py-2 whitespace-nowrap uppercase underline cursor-pointer"
        >
          Register
        </a>
      </div>
    </form>
  );
}
