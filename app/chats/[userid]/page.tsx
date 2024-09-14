"use client";
import CustomTable from "@/components/CustomTable";
import useAuth from "@/hooks/useAuth";
import WithSidebar from "@/layouts/WithSidebar";
import { useActiveChat } from "@/stores/activeChat";
import { TableCell } from "@mui/material";
import axios from "axios";
import Link from "next/link";
import { useParams, usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import Swal from "sweetalert2";

type Chat = {
  _id: string;
  title: string;
  user_email: string;
  messages: string[];
  created_at: string;
};

const headCells = [
  {
    id: "title",
    numeric: false,
    label: "Title",
  },
  {
    id: "user_email",
    numeric: true,
    label: "User Email",
  },
  {
    id: "created_at",
    numeric: true,
    label: "Created At",
  },
  {
    id: "actions",
    numeric: true,
    label: "Actions",
  },
];

export default function Chats() {
  const router = useRouter();
  const params = useParams();
  const [chats, setChats] = useState<Chat[]>([]);
  const [token, session] = useAuth();
  const [totalRecords, setTotalRecords] = useState(0);
  const { setActiveChat } = useActiveChat();

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  useEffect(() => {
    setActiveChat({
      id: "",
      title: "",
      user_email: "",
      messages: [],
      created_at: "",
    });
  }, []);

  useEffect(() => {
    if (!session) return;

    const fetchTotalRecords = async () => {
      try {
        const response = await axios.post(
          process.env.NEXT_PUBLIC_API_URL + `/chats/count`,
          {
            user_id: params.userid,
          },
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        setTotalRecords(response.data.data);
      } catch (error: any) {
        const data = error.response;
        if (data) {
          console.log(data.message);
          toast.error(data.message);
        }
      }
    };

    fetchTotalRecords();
  }, [params.userid, session, token]);

  useEffect(() => {
    if (!session) return;

    const fetchUsers = async () => {
      try {
        const response = await axios.post(
          process.env.NEXT_PUBLIC_API_URL +
            `/chats?page=${page}&limit=${rowsPerPage}`,
          {
            user_id: params.userid,
          },
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        const records = response.data.data;
        const sortedRecords = records.sort(
          (a: any, b: any) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setChats(sortedRecords);
      } catch (error: any) {
        const data = error.response;
        if (data) {
          console.log(data.message);
          toast.error(data.message);
        }
      }
    };

    fetchUsers();
  }, [page, params.userid, rowsPerPage, session, token]);

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (!session) return null;
  if (session.role !== "admin") router.push("/");

  const handleDelete = async (id: string) => {
    const result = await Swal.fire({
      title: "Are you sure?",
      text: "You are deleting users data, you won't be able to revert this!",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Yes, delete it!",
      cancelButtonText: "No, cancel!",
    });

    if (!result.isConfirmed) return;

    try {
      await axios.delete(process.env.NEXT_PUBLIC_API_URL + `/chats/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      toast.success("Chat deleted successfully");

      const newChats = chats.filter((chat) => chat._id !== id);
      setChats(newChats);
    } catch (error: any) {
      const data = error.response;
      if (data) {
        console.log(data.message);
        toast.error(data.message);
      }
    }
  };

  return (
    <WithSidebar>
      <div className="container mx-auto p-4 h-full overflow-auto scrollbar">
        <h1 className="text-slate-900 text-center mt-6 mb-8 font-bold text-3xl md:text-left">
          Chats for selected user
        </h1>

        <CustomTable
          data={chats}
          headCells={headCells}
          tableRow={(row: Chat, index: number) => (
            <>
              <TableCell>{row.title}</TableCell>
              <TableCell align="right">{row.user_email}</TableCell>
              <TableCell align="right">
                {new Date(row.created_at).toLocaleString()}
              </TableCell>
              <TableCell align="right">
                <Link
                  href={`/singleChat/${row._id}`}
                  className="text-blue-500 hover:underline"
                >
                  View Conversation
                </Link>
                <button
                  className="text-red-500 ml-2 hover:underline border-none bg-transparent"
                  onClick={() => handleDelete(row._id)}
                >
                  Delete
                </button>
              </TableCell>
            </>
          )}
          totalRecords={totalRecords}
          handleChangePage={handleChangePage}
          handleChangeRowsPerPage={handleChangeRowsPerPage}
          page={page}
          rowsPerPage={rowsPerPage}
        />
      </div>
    </WithSidebar>
  );
}
