local directory = os.getenv("PW_TELEPORT_PROBE_DIR")
if not directory then
    return
end

local route = dofile(directory .. "/route.lua")
local session_file = directory .. "/session"
local ready_file = directory .. "/ready"
local screen_file = directory .. "/screen.pending"
local enter_world = PlayerEnterWorld
local leave_world = PlayerLeaveWorld
local heartbeat = EventPlayerHeartBeat
local generation = 0
local session
local dark = false

assert(type(game__Packet) == "function" and type(game__Send) == "function")
print("teleport UX display API ready")

local function read_line(path)
    local input = io.open(path, "r")
    if not input then
        return
    end
    local line = input:read("*l")
    input:close()
    return line
end

local function show_wait(role_id, enabled)
    if dark == enabled then
        return
    end
    game__Packet(0, 0, 0)
    game__Packet(1, 1, 392)
    game__Packet(1, 2, 0)
    game__Packet(1, 2, 1)
    game__Packet(1, 2, enabled and 1 or 0)
    game__Send(role_id)
    game__Packet(0, 0, 0)
    dark = enabled
    print(os.date("%Y-%m-%dT%H:%M:%S%z") .. " teleport UX screen " .. (enabled and "on" or "off")
        .. " role " .. role_id)
end

function PlayerEnterWorld(role_id)
    enter_world(role_id)
    if role_id ~= route.role_id or game__GetWorldTag() ~= route.source then
        return
    end
    generation = generation + 1
    local token = os.time() .. ":" .. generation
    local output = io.open(session_file .. ".tmp", "w")
    if not output then
        return
    end
    output:write(token, "\n")
    if output:close() and os.rename(session_file .. ".tmp", session_file) then
        session = token
        print("teleport source session ready for role " .. role_id)
    end
end

function PlayerLeaveWorld(role_id)
    if role_id == route.role_id and session then
        session = nil
        dark = false
        os.remove(session_file)
    end
    leave_world(role_id)
end

function EventPlayerHeartBeat(role_id, tick)
    heartbeat(role_id, tick)
    if role_id ~= route.role_id or not session then
        return
    end
    if read_line(ready_file) == session and os.remove(ready_file) then
        show_wait(role_id, false)
        print("teleport continuation for role " .. role_id .. " worldtag " .. route.destination)
        game__PlayerTeleport(role_id, route.destination, route.x, route.y, route.z)
        return
    end
    local token, expires = (read_line(screen_file) or ""):match("^(%S+) (%d+)$")
    show_wait(role_id, token == session and tonumber(expires) > os.time())
end
