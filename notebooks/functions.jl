RatedPower = 15 # wind turbine rated power in MW
breakpts = [2.795492381350064, 7, 10.590504911515957, 25]
f1_coef = [0.0800404  -0.229128  0.0403189  0.0112332]
f2_coef = [-0.0352525  -0.346  0.082  0.008]
coefs = hcat(zeros(4), f1_coef', f2_coef', vcat(RatedPower,zeros(3)), zeros(4))

function Turbine_PC(x::Float64, breakpts::Vector{Float64}, coefs::Matrix{Float64})
       @assert(issorted(breakpts))
       @assert(length(breakpts) == size(coefs,2)-1)
       b = searchsortedfirst(breakpts, x)
       return sum(coefs[i,b]*x^(i-1) for i=1:size(coefs,1))
end

function Interpolate_States(KernTree)
    States = reduce(hcat, range(KernTree.state[:,1], KernTree.state[:,2],5));
    for i=2:24-1
        States = hcat(States, reduce(hcat, range(KernTree.state[:,i], KernTree.state[:,i+1],5))[:,2:5])
    end
    for i=1:3
        States = hcat(States, KernTree.state[:,24]+i*(KernTree.state[:,24]-KernTree.state[:,1])/4)
    end
    States
end

function save_control_solution(SC, kW, kB)
    SoCSol = DataFrame(reduce(hcat,[hcat(value.(SC[:,s]))*PowerBase for s in S2]), ["SoC $s2" for s2 in S2])
    kWSol = DataFrame(reduce(hcat,[hcat(value.(kW[:,s])) for s in S2]), ["kW $s2" for s2 in S2])
    kBSol = DataFrame(reduce(hcat,[hcat(value.(kB[:,s])) for s in S2]), ["kB $s2" for s2 in S2])
    CtrlSol = hcat(SoCSol, kWSol, kBSol)
    CSV.write("control_solution.csv", CtrlSol)
    return nothing
end

function CalDis(coord1, coord2)
    Lat1 = coord1[1]
    Lon1 = coord1[2]
    Lat2 = coord2[1]
    Lon2 = coord2[2]
    acos((sin(deg2rad(Lat1))*sin(deg2rad(Lat2)))+(cos(deg2rad(Lat1))*cos(deg2rad(Lat2)))*(cos(deg2rad(Lon2) - deg2rad(Lon1))))*6371
end
;