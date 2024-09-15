"use client";
import useAuth from "@/hooks/useAuth";
import WithSidebar from "@/layouts/WithSidebar";
import axios from "axios";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import Swal from "sweetalert2";

export default function Knowledge() {
  const [token, session] = useAuth();
  const [initials, setInitials] = useState<string | null>(null);
  const [name, setName] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!session) {
      return;
    }

    const { name } = session;
    setInitials(
      name
        .split(" ")
        .map((n) => n[0])
        .join("")
    );

    setName(name);
    setEmail(session.email);
  }, [token, session]);

  if (!session) {
    return null;
  }

  async function handleChangeName() {
    const { value: formValues } = await Swal.fire({
      title: "Change Name",
      html:
        '<input id="swal-input1" class="swal2-input" placeholder="Enter new name">' +
        '<input id="swal-input2" type="password" class="swal2-input mt-4" placeholder="Enter password">',
      focusConfirm: false,
      preConfirm: () => {
        const name = (
          document.getElementById("swal-input1") as HTMLInputElement
        ).value;
        const password = (
          document.getElementById("swal-input2") as HTMLInputElement
        ).value;
        if (!name || !password) {
          Swal.showValidationMessage("Please enter all fields");
          return false;
        }
        return { name, password };
      },
    });

    if (!formValues) return;

    const { name, password } = formValues;

    try {
      const response = await axios.post(
        process.env.NEXT_PUBLIC_API_URL + "/auth/change-name",
        {
          name,
          password,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = response.data;

      if (!data.success) {
        toast.error(data.message);
        return;
      }
      toast.success(data.message);

      localStorage.removeItem("token");
      router.replace("/login");

      setName(name);
    } catch (error: any) {
      toast.error(error.response.data.message);
      return;
    }
  }

  async function handleChangeEmail() {
    const { value: formValues } = await Swal.fire({
      title: "Change Password",
      html:
        '<input id="swal-input1" type="password" class="swal2-input w-full max-w-xs px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Enter current password">' +
        '<input id="swal-input2" type="password" class="swal2-input mt-4 w-full max-w-xs px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Enter new password">' +
        '<input id="swal-input3" type="password" class="swal2-input mt-4 w-full max-w-xs px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Confirm new password">',
      focusConfirm: false,
      showCancelButton: true,
      preConfirm: () => {
        const currentPassword = (
          document.getElementById("swal-input1") as HTMLInputElement
        ).value;
        const newPassword = (
          document.getElementById("swal-input2") as HTMLInputElement
        ).value;
        const confirmPassword = (
          document.getElementById("swal-input3") as HTMLInputElement
        ).value;
        if (!currentPassword || !newPassword || !confirmPassword) {
          Swal.showValidationMessage("Please enter all fields");
          return false;
        }
        if (newPassword !== confirmPassword) {
          Swal.showValidationMessage("Passwords do not match");
          return false;
        }
        return { currentPassword, newPassword };
      },
    });

    if (!formValues) return;

    const { currentPassword, newPassword } = formValues;

    try {
      const response = await axios.post(
        process.env.NEXT_PUBLIC_API_URL + "/auth/change-password",
        {
          currentPassword,
          newPassword,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = response.data;

      if (!data.success) {
        toast.error(data.message);
        return;
      }
      toast.success(data.message);

      localStorage.removeItem("token");
      router.replace("/login");
    } catch (error: any) {
      toast.error(error.response.data.message);
      return;
    }
  }

  return (
    <WithSidebar>
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col items-center p-6 bg-white rounded-lg">
          <div className="w-20 h-20 flex items-center justify-center bg-gray-500 rounded-full text-white text-2xl font-bold mb-4">
            {initials}
          </div>
          <h2 className="text-xl font-semibold mb-4">{name}</h2>
          <p className="text-gray-500 mb-4">{email}</p>
          <div className="space-x-4">
            <button
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              onClick={handleChangeName}
            >
              Change Name
            </button>
            <button
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              onClick={handleChangeEmail}
            >
              Change Password
            </button>
          </div>
        </div>
      </div>
    </WithSidebar>
  );
}
