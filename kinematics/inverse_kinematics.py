import math
from forward_kinematics import forward_kinematics


def forward_adapter(q):
    base_deg = math.degrees(q[0])
    shoulder_deg = math.degrees(q[1])
    elbow_deg = math.degrees(q[2])
    wrist_deg = math.degrees(q[3])

    fk_result = forward_kinematics(base_deg, shoulder_deg, elbow_deg, wrist_deg)
    x, y, z = fk_result["tool_tip"]
    return [x, y, z]


def _solve_3x3(matrix, vector):  # gaussian elimination with partial pivoting
    rows = [list(row) + [value] for row, value in zip(matrix, vector)]

    for col in range(3):
        pivot = max(range(col, 3), key=lambda r: abs(rows[r][col]))
        rows[col], rows[pivot] = rows[pivot], rows[col]

        if abs(rows[col][col]) < 1e-15:
            return [0.0, 0.0, 0.0]

        divisor = rows[col][col]
        rows[col] = [v / divisor for v in rows[col]]

        for r in range(3):
            if r == col:
                continue
            factor = rows[r][col]
            rows[r] = [
                rows[r][i] - factor * rows[col][i]
                for i in range(4)
            ]

    return [rows[i][3] for i in range(3)]


def solve_ik(
        target,
        initial,
        limits,
        forward,
        slide_joints=None,
        iterations=180,
        tolerance=0.0005,
):
    """
    Inverse kinematics solver

    Args:
        target: [x, y, z] target position in meters
        initial: joint values in radians <-- not degrees
        limits: [(min, max), ...] joint limits in radians
        forward: function(q) -> (x, y, z) tool-tip position
        slide_joints: optional list of bools for prismatic joints
        iterations: iterations per restart
        tolerance: stopping threshold in meters

    Returns:
        {
            "q": best joint vector,
            "converged": bool,
            "error": final error magnitude,
            "iterations": total iterations used
        }
    """
    target = list(target)
    initial = list(initial)
    limits = [tuple(pair) for pair in limits]
    joint_count = len(initial)

    if len(target) != 3 or not all(math.isfinite(x) for x in target):
        raise ValueError("target must be 3 finite numbers")

    if len(limits) != joint_count:
        raise ValueError("one limit pair per joint is required")

    if any(
            len(pair) != 2
            or not math.isfinite(pair[0])
            or not math.isfinite(pair[1])
            or pair[0] > pair[1]
            for pair in limits
    ):
        raise ValueError("bad joint limits")

    if slide_joints is None:
        slide_joints = [False] * joint_count
    if len(slide_joints) != joint_count:
        raise ValueError("slide_joints length must match joint_count")

    def clamp(q):
        out = []
        for i, value in enumerate(q):
            lo, hi = limits[i]
            out.append(max(lo, min(hi, value)))
        return out

    def position(q):
        pos = forward(q)
        pos = list(pos)
        if len(pos) != 3 or not all(math.isfinite(x) for x in pos):
            raise ValueError("forward(q) must return 3 finite numbers")
        return pos

    best_q = clamp(initial)
    best_error = float("inf")
    iterations_used = 0

    # Try initial pose
    for trial in range(5):
        if trial == 0:
            q = clamp(initial)
        else:
            q = clamp([
                initial[i] + math.sin((trial + 1) * (i + 2)) * (0.05 if slide_joints[i] else 0.6)
                for i in range(joint_count)
            ])

        for _ in range(iterations):
            iterations_used += 1
            current_pos = position(q)
            error_vec = [
                target[i] - current_pos[i]
                for i in range(3)
            ]
            error_mag = math.sqrt(sum(v * v for v in error_vec))

            if error_mag < best_error:
                best_error = error_mag
                best_q = q[:]

            if error_mag < tolerance:
                return {
                    "q": best_q[:],
                    "converged": True,
                    "error": error_mag,
                    "iterations": iterations_used,
                }

            columns = []
            for joint_idx in range(joint_count):
                step = 1e-5
                lo, hi = limits[joint_idx]
                if q[joint_idx] + step > hi:
                    step = -step

                dq = q[:]
                dq[joint_idx] += step
                p2 = position(dq)
                deriv = [
                    (p2[axis] - current_pos[axis]) / step
                    for axis in range(3)
                ]
                columns.append(deriv)

            # Construct A = J * J^T + damping * I
            damping = 1e-4
            A = [
                [
                    sum(columns[j][row] * columns[k][col]
                        for j in range(joint_count)
                        for k in range(joint_count)
                        if j == k and False)  # just placeholder, replaced below
                    for col in range(3)
                ]
                for row in range(3)
            ]

            # Correct A = J * J^T + damping I
            for row in range(3):
                for col in range(3):
                    s = 0.0
                    for joint_idx in range(joint_count):
                        s += columns[joint_idx][row] * columns[joint_idx][col]
                    A[row][col] = s + (damping if row == col else 0.0)

            # Solve A * v = e
            v = _solve_3x3(A, error_vec)

            # Update joints: q_next = q + J^T * v
            next_q = []
            for joint_idx in range(joint_count):
                delta = 0.0
                for axis in range(3):
                    delta += columns[joint_idx][axis] * v[axis]
                delta = max(-0.15, min(0.15, delta))
                next_q.append(q[joint_idx] + delta)

            q = clamp(next_q)

    return {
        "q": best_q[:],
        "converged": False,
        "error": best_error,
        "iterations": iterations_used,
    }


if __name__ == "__main__":
    # 1. Define a target position [x, y, z] in meters where you want the robot arm to reach
    target_position = [0.1, 0.0, 0.2]

    # 2. Provide an initial guess for your 4 joint angles (in radians)
    initial_joints = [0.0, 0.0, 0.0, 0.0]

    # 3. Define the physical joint limits (min, max) for each of the 4 joints in radians
    #    (e.g., -pi to pi for rotation, or custom limits based on your robot design)
    joint_limits = [
        (-3.14, 3.14),
        (-1.57, 1.57),
        (-1.57, 1.57),
        (-3.14, 3.14)
    ]

    print(f"Solving IK for target: {target_position}...")

    # 4. Run the solver by passing your forward_adapter function
    result = solve_ik(
        target=target_position,
        initial=initial_joints,
        limits=joint_limits,
        forward=forward_adapter
    )

    # 5. Print the results
    print("\n--- IK Results ---")
    print(f"Converged: {result['converged']}")
    print(f"Final Error: {result['error']:.6f} meters")
    print(f"Iterations Used: {result['iterations']}")
    print(f"Best Joint Angles (radians): {result['q']}")

    # Optional: Convert the resulting joint angles back to degrees to see them clearly
    degrees_q = [math.degrees(angle) for angle in result['q']]
    print(f"Best Joint Angles (degrees): {degrees_q}")