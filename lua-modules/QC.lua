-- For Questionable Content Wiki
-- https://questionablecontent.fandom.com/wiki/Module:QC
--
-- Lua links:
-- https://en.wikipedia.org/wiki/Wikipedia:Lua
-- https://www.mediawiki.org/wiki/Extension:Scribunto/Lua_reference_manual

local p = {}

local rootUrl = "https://www.questionablecontent.net"
local titles = mw.loadData('Module:QC/titles')

-- num : comic number, mandatory argument
-- Returns URL to a comic of given number.
function p.viewUrl(num)
    return rootUrl .. "/view.php?comic=" .. num
end

-- num : comic number, mandatory argument
-- Returns comic title corresponding to given comic number.
function p.getTitle(num)
    local number = tonumber(num)
    local t = titles[number]
    if not t
    then
        t = num
    else
        -- comics after 3649 do not have prefix "Number "
        if number <= 3649
        then
            -- TODO special case for numbers <100, like "Number Ninety Nine: Almost Psychic"
            t = "Number " .. num .. ': ' .. t
        else
            t = num .. ': ' .. t
        end
    end
    return t
end

-- url  : a valid URL to create a link from, mandatory argument
-- text : custom link text OR nil
-- Returns wikitext for a link with given URL.
function p.link(url, text)
    if not text
    then
        return '[' .. url .. ']'
    else
        return '[' .. url .. ' ' .. text .. ']'
    end
end

-- num  : comic number OR nil
-- text : custom link text OR nil
-- Returns wikitext for a comic link of given number.
-- If comic number is not provided, link to home page of QC is returned.
function p.comicLink(num, text)
    if not num
    then
        return p.link(rootUrl, text)
    end
    local u = p.viewUrl(num)
    local t = text or p.getTitle(num)
    return p.link(u, t)
end

-- urlPart : subpage of questionablecontent.net OR nil
-- text    : custom link text OR nil
-- Returns wikitext for a link to a page which is not view.php.
function p.customLink(urlPart, text)
    local u = rootUrl
    if urlPart ~= nil
    then
        u = u .. '/' .. urlPart
    end
    local t = text or urlPart
    return p.link(u, t)
end

-- Main function
function p._qc(num, text, custom)
    local code = ''
    if custom == 'custom'
    then
        code = p.customLink(num, text)
    else
        code = p.comicLink(num, text)
    end
    return '<span class="plainlinks">' .. code .. '</span>'
end

-- Helper function
function p.unwrapArg(arg)
    if not arg or #arg == 0
    then
        return nil
    else
        return arg
    end
end

-- Helper function
function p.qc(frame)
    local num = p.unwrapArg(frame.args[1])
    local text = p.unwrapArg(frame.args[2])
    local custom = p.unwrapArg(frame.args[3])
    return p._qc(num, text, custom)
end

return p
--[[Category:Lua Modules]]
