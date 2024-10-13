"use client";

import useAuth from "@/hooks/useAuth";
import WithSidebar from "@/layouts/WithSidebar";
import axios from "axios";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import TableCell from "@mui/material/TableCell";
import CustomTable, { HeadCell } from "@/components/CustomTable";
import Swal from "sweetalert2";
import { FaFileCirclePlus, FaSpinner } from "react-icons/fa6";

type Doc = {
  _id: string;
  title: string;
  created_at: string;
};

const headCells: readonly HeadCell[] = [
  {
    id: "title",
    numeric: false,
    label: "Doc title",
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

export default function Users() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const [docs, setDocs] = useState<Doc[]>([]);
  const [nonAccessibleDocs, setNonAccessibleDocs] = useState<Doc[]>([]);
  const [token, session] = useAuth();
  const [isAdding, setIsAdding] = useState(false);
  const [shouldUpdateDocs, setShouldUpdateDocs] = useState(false);

  const [recordsCount, setRecordsCount] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  useEffect(() => {
    if (!session) return;

    const fetchRecordCount = async () => {
      try {
        const response = await axios.get(
          `${process.env.NEXT_PUBLIC_API_URL}/documents/count/${params.userid}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        setRecordsCount(response.data.data);
      } catch (error: any) {
        const data = error.response;
        if (data) {
          console.log(data.message);
          toast.error(data.message);
        }
      }
    };

    const fetchRecords = async () => {
      try {
        const response = await axios.get(
          `${process.env.NEXT_PUBLIC_API_URL}/documents/allowed-docs/${params.userid}?page=${page}&limit=${rowsPerPage}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        const users = response.data.data;
        const sortedUsers = users.sort(
          (a: Doc, b: Doc) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setDocs(sortedUsers);
      } catch (error: any) {
        const data = error.response;
        if (data) {
          console.log(data.message);
          toast.error(data.message);
        }
      }
    };

    const fetchNonAccessibleDocs = async () => {
      try {
        const response = await axios.get(
          `${process.env.NEXT_PUBLIC_API_URL}/documents/not-allowed-docs/${params.userid}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        const nonAccessibleDocs = response.data.data;
        const sortedDocs = nonAccessibleDocs.sort(
          (a: Doc, b: Doc) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setNonAccessibleDocs(sortedDocs);
      } catch (error: any) {
        const data = error.response;
        if (data) {
          console.log(data.message);
          toast.error(data.message);
        }
      }
    };

    fetchRecordCount();
    fetchRecords();
    fetchNonAccessibleDocs();
  }, [page, params.userid, rowsPerPage, session, token, shouldUpdateDocs]);

  const handleChangePage = (_: unknown, newPage: number) => {
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

  const handleRemove = async (id: string) => {
    const result = await Swal.fire({
      title: "Are you sure?",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Yes",
      cancelButtonText: "No, cancel!",
    });

    if (!result.isConfirmed) return;

    try {
      await axios.delete(
        process.env.NEXT_PUBLIC_API_URL + `/users/${params.userid}/${id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setRecordsCount(recordsCount - 1);

      setShouldUpdateDocs(!shouldUpdateDocs);

      toast.success("Access removed successfully");
    } catch (error: any) {
      const data = error.response;
      if (data) {
        console.log(data.message);
        toast.error(data.message);
      }
    }
  };

  const handleAddDocument = async () => {
    const { value: documentId } = await Swal.fire({
      title: "Create Document",
      html: `<select id="swal-input1" class="swal2-input w-full max-w-xs px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Enter document title">
        <option disabled selected value="">Select a document</option>
        ${
          nonAccessibleDocs.length === 0
            ? "<option disabled value=''>No documents available</option>"
            : nonAccessibleDocs
                .map(
                  (doc) => `<option value="${doc._id}">${doc.title}</option>`
                )
                .join("")
        }
      </select>`,
      focusConfirm: false,
      showCancelButton: true,
      preConfirm: () => {
        const documentID = (
          document.getElementById("swal-input1") as HTMLInputElement
        ).value;

        if (!documentID) {
          Swal.showValidationMessage("Please select a valid option");
          return false;
        }
        return documentID;
      },
    });

    if (!documentId) return;

    setIsAdding(true);

    try {
      await axios.put(
        `${process.env.NEXT_PUBLIC_API_URL}/users/${params.userid}/${documentId}`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setShouldUpdateDocs(!shouldUpdateDocs);

      toast.success("Document added successfully");
    } catch (error: any) {
      const data = error.response;
      if (data) {
        console.log(data.message);
        toast.error(data.message);
      }
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <WithSidebar>
      <div className="container mx-auto p-4 h-full overflow-auto scrollbar">
        <div className="flex items-center justify-between">
          <h1 className="text-slate-900 text-center mt-6 mb-8 font-bold text-3xl md:text-left">
            Accessible Documents for {searchParams.get("name")}
          </h1>

          <button
            className="flex items-center justify-between gap-2 p-2 px-4 rounded text-white bg-blue-500 hover:bg-blue-600 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={(e) => {
              e.preventDefault();
              handleAddDocument();
            }}
            disabled={isAdding}
          >
            {isAdding ? (
              <>
                <FaSpinner className="animate-spin" /> Adding
              </>
            ) : (
              <>
                <FaFileCirclePlus /> Add document
              </>
            )}
          </button>
        </div>

        <CustomTable
          data={docs}
          headCells={headCells}
          tableRow={(row: Doc, index: number) => (
            <>
              <TableCell>{row.title}</TableCell>
              <TableCell align="right">
                {new Date(row.created_at).toLocaleString()}
              </TableCell>
              <TableCell align="right">
                <button
                  className="text-red-500 ml-2 hover:underline border-none bg-transparent"
                  onClick={() => handleRemove(row._id)}
                >
                  Remove
                </button>
              </TableCell>
            </>
          )}
          totalRecords={recordsCount}
          handleChangePage={handleChangePage}
          handleChangeRowsPerPage={handleChangeRowsPerPage}
          page={page}
          rowsPerPage={rowsPerPage}
        />
      </div>
    </WithSidebar>
  );
}
