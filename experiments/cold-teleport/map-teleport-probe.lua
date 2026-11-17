local directory = os.getenv("PW_TELEPORT_PROBE_DIR")
if not directory then
    return
end

local route = dofile(directory .. "/route.lua")
local session_file = directory .. "/session"
local ready_file = directory .. "/ready"
local enter_world = PlayerEnterWorld
local leave_world = PlayerLeaveWorld
local heartbeat = EventPlayerHeartBeat
local generation = 0
local session

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
        os.remove(session_file)
    end
    leave_world(role_id)
end

function EventPlayerHeartBeat(role_id, tick)
    heartbeat(role_id, tick)
    if role_id ~= route.role_id or not session then
        return
    end
    local input = io.open(ready_file, "r")
    if not input then
        return
    end
    local token = input:read("*l")
    input:close()
    if token == session and os.remove(ready_file) then
        print("teleport continuation for role " .. role_id .. " worldtag " .. route.destination)
        game__PlayerTeleport(role_id, route.destination, route.x, route.y, route.z)
    end
end
