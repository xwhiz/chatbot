"use client";
import WithSidebar from "@/layouts/WithSidebar";
import { FaEdit, FaRegEdit, FaTrash } from "react-icons/fa";
import { FaPenToSquare } from "react-icons/fa6";

import { Table, Thead, Tbody, Tr, Td } from "react-super-responsive-table";
import "react-super-responsive-table/dist/SuperResponsiveTableStyle.css";

export default function Chats() {
  return (
    <WithSidebar>
      <div className="container mx-auto p-4 h-full overflow-auto scrollbar">
        <h1 className="text-slate-900 text-center mt-6 mb-8 font-bold text-3xl md:text-left">
          Chats
        </h1>

        <div className="bg-white p-8 rounded shadow-lg">
          <Table className="w-full rounded overflow-hidden">
            <Thead>
              <Tr className="bg-slate-200">
                <Td className="p-2">chatID</Td>
                <Td className="p-2">Chat Title</Td>
                <Td className="p-2">Date Created</Td>
                <Td className="p-2">Actions</Td>
              </Tr>
            </Thead>
            <Tbody>
              <Tr>
                <Td className="p-2">1</Td>
                <Td className="p-2">Chat title</Td>
                <Td className="p-2">2022-03-15</Td>
                <Td className="p-2 flex gap-2">
                  <button className="text-white bg-blue-600 px-4 py-2 rounded hover:bg-blue-500">
                    <FaPenToSquare />
                  </button>

                  <button className="text-white bg-red-600 px-4 py-2 rounded hover:bg-red-500">
                    <FaTrash />
                  </button>
                </Td>
              </Tr>
              <Tr>
                <Td className="p-2">2</Td>
                <Td className="p-2">Chat title</Td>
                <Td className="p-2">2022-03-15</Td>
                <Td className="p-2 flex gap-2">
                  <button className="text-white bg-blue-600 px-4 py-2 rounded hover:bg-blue-500">
                    <FaPenToSquare />
                  </button>

                  <button className="text-white bg-red-600 px-4 py-2 rounded hover:bg-red-500">
                    <FaTrash />
                  </button>
                </Td>
              </Tr>
              <Tr>
                <Td className="p-2">3</Td>
                <Td className="p-2">Chat title</Td>
                <Td className="p-2">2022-03-15</Td>
                <Td className="p-2 flex gap-2">
                  <button className="text-white bg-blue-600 px-4 py-2 rounded hover:bg-blue-500">
                    <FaPenToSquare />
                  </button>

                  <button className="text-white bg-red-600 px-4 py-2 rounded hover:bg-red-500">
                    <FaTrash />
                  </button>
                </Td>
              </Tr>
            </Tbody>
          </Table>

          {/* Pagination to be added */}
        </div>
      </div>
    </WithSidebar>
  );
}
