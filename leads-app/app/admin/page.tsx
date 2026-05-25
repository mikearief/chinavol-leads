import { revalidatePath } from "next/cache";
import { listUsers, setUserApproval } from "@/lib/db";
import { requireAdminSession } from "@/lib/session";

async function setApproval(formData: FormData) {
  "use server";
  await requireAdminSession();
  const userId = String(formData.get("userId"));
  const approved = formData.get("approved") === "true";
  await setUserApproval(userId, approved);
  revalidatePath("/admin");
}

export default async function AdminPage() {
  await requireAdminSession();
  const users = await listUsers();

  return (
    <>
      <div className="page-header">
        <h1>User Management</h1>
        <p className="subtitle">Approve or revoke ChinaVol Pro access</p>
      </div>

      <div className="signals-table-wrapper">
        <table className="signals-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Role</th>
              <th>Approved</th>
              <th>Last Login</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.$id}>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td>{user.approved || user.role === "admin" ? "Yes" : "No"}</td>
                <td>{user.last_login ? new Date(user.last_login).toLocaleString() : "-"}</td>
                <td>
                  {user.role === "admin" ? (
                    <span className="muted">Admin</span>
                  ) : (
                    <form action={setApproval}>
                      <input type="hidden" name="userId" value={user.$id} />
                      <input
                        type="hidden"
                        name="approved"
                        value={user.approved ? "false" : "true"}
                      />
                      <button className="btn btn-sm" type="submit">
                        {user.approved ? "Revoke" : "Approve"}
                      </button>
                    </form>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
