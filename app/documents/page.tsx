"use client";
import CustomTable, { HeadCell } from "@/components/CustomTable";
import useAuth from "@/hooks/useAuth";
import WithSidebar from "@/layouts/WithSidebar";
import { TableCell } from "@mui/material";
import axios from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FaFileCirclePlus, FaFolderPlus, FaSpinner } from "react-icons/fa6";
import "react-super-responsive-table/dist/SuperResponsiveTableStyle.css";
import { toast } from "react-toastify";
import Swal from "sweetalert2";

type Document = {
  _id: string;
  title: string;
  created_at: string;
};

const headCells: readonly HeadCell[] = [
  {
    id: "title",
    numeric: false,
    label: "Title",
  },
  {
    id: "created_at",
    numeric: true,
    label: "Created At",
  },
  {
    id: "_id",
    numeric: true,
    label: "Actions",
  },
];

export default function Documents() {
  const router = useRouter();
  const [records, setRecords] = useState<Document[]>([]);
  const [token, session] = useAuth();
  const [totalRecords, setTotalRecords] = useState(0);
  const [uploading, setUploading] = useState(false);

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  useEffect(() => {
    if (!session) return;

    const fetchTotalRecords = async () => {
      try {
        const response = await axios.get(
          process.env.NEXT_PUBLIC_API_URL + "/documents/count",
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
  }, [session, token]);

  useEffect(() => {
    if (!session) return;

    const fetchRecords = async () => {
      try {
        const response = await axios.get(
          process.env.NEXT_PUBLIC_API_URL +
            `/documents?page=${page}&limit=${rowsPerPage}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        const records = response.data.data;
        const sortedRecords = records.sort(
          (a: Document, b: Document) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setRecords(sortedRecords);
      } catch (error: any) {
        const data = error.response;
        if (data) {
          console.log(data.message);
          toast.error(data.message);
        }
      }
    };

    fetchRecords();
  }, [page, rowsPerPage, session, token]);

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
      text: "You are deleting the user and their chats, you won't be able to revert this!",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Yes, delete it!",
      cancelButtonText: "No, cancel!",
    });

    if (!result.isConfirmed) return;

    try {
      await axios.delete(process.env.NEXT_PUBLIC_API_URL + `/documents/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setTotalRecords(totalRecords - 1);

      const response = await axios.get(
        process.env.NEXT_PUBLIC_API_URL +
          `/documents?page=${page}&limit=${rowsPerPage}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      const users = response.data.data;
      const sortedUsers = users.sort(
        (a: any, b: any) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setRecords(sortedUsers);

      toast.success("User deleted successfully");
    } catch (error: any) {
      const data = error.response;
      if (data) {
        console.log(data.message);
        toast.error(data.message);
      }
    }
  };

  const handleCreateDocument = async () => {
    const { value: formValues } = await Swal.fire({
      title: "Create Document",
      html:
        '<input id="swal-input1" class="swal2-input w-full max-w-xs px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Enter document title">' +
        '<input id="swal-input2" type="file" class="swal2-file mt-4 w-full max-w-xs px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" accept="application/pdf">',
      focusConfirm: false,
      showCancelButton: true,
      preConfirm: () => {
        const title = (
          document.getElementById("swal-input1") as HTMLInputElement
        ).value;
        const file = (
          document.getElementById("swal-input2") as HTMLInputElement
        ).files?.[0];
        if (!title || !file) {
          Swal.showValidationMessage("Please enter a title and select a file");
          return false;
        }
        return { title, file };
      },
    });

    if (!formValues) return;

    const { title, file } = formValues;

    if (!title || !file) return;

    if (title.length === 0 || file.size === 0) {
      toast.error("Please enter a title and select a file");
      return;
    }

    // file should be pdf
    if (file.type !== "application/pdf") {
      toast.error("Please select a pdf file");
      return;
    }

    const formData = new FormData();
    formData.append("title", title);
    formData.append("file", file);

    setUploading(true);
    try {
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/documents`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setTotalRecords(totalRecords + 1);

      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/documents?page=${page}&limit=${rowsPerPage}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const documents = response.data.data;
      const sortedDocuments = documents.sort(
        (a: Document, b: Document) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );

      setRecords(sortedDocuments);

      toast.success("Document created successfully");
    } catch (error: any) {
      const data = error.response;
      console.log(error);
      if (data) {
        console.log(data.message);
        toast.error(data.message);
      }
    } finally {
      setUploading(false);
    }
  };

  const handleViewDocument = async (id: string) => {
    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/documents/${id}`,
        {
          responseType: "blob",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      const url = window.URL.createObjectURL(
        new Blob([response.data], { type: "application/pdf" })
      );
      window.open(url, "_blank");
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
        <div className="flex items-center justify-between">
          <h1 className="text-slate-900 text-center mt-6 mb-8 font-bold text-3xl md:text-left">
            Documents
          </h1>

          <button
            className="flex items-center justify-between gap-2 p-2 px-4 rounded text-white bg-blue-500 hover:bg-blue-600 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={(e) => {
              e.preventDefault();
              handleCreateDocument();
            }}
            disabled={uploading}
          >
            {uploading ? (
              <>
                <FaSpinner className="animate-spin" /> Uploading
              </>
            ) : (
              <>
                <FaFileCirclePlus /> Create Document
              </>
            )}
          </button>
        </div>

        <CustomTable
          data={records}
          headCells={headCells}
          tableRow={(row: Document, index: number) => (
            <>
              <TableCell>{row.title}</TableCell>
              <TableCell align="right">
                {new Date(row.created_at).toLocaleString()}
              </TableCell>
              <TableCell align="right">
                <button
                  className="text-blue-500 hover:underline"
                  onClick={() => handleViewDocument(row._id)}
                >
                  View Document
                </button>
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
