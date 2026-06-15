# 1. Introduction

## 1.1 Background

Delta-type parallel robots are widely used in high-speed pick-and-place, packaging, and light assembly because their parallel kinematic structure keeps actuators at the fixed base and moving mass low, which in turn gives fast, precise, and computationally simple motion. This same structure, however, imposes well-known limits: the reachable workspace is only a small fraction of the robot's physical footprint, the mechanism approaches singular configurations near the boundary of that workspace, the end-effector cannot rotate without additional hardware, and a fault in any single limb disables the entire machine. These limitations become significant barriers in tasks that require deep or variable reach, in mobile or field deployments where the robot must change configuration to fit its environment, and in settings where continued operation after a partial failure is necessary.

This work addresses these limitations through a single underlying design philosophy: treating the manipulator not as a fixed assembly but as a small family of standardized, interchangeable mechanical and electrical "modules" that can be combined in different arrangements around a central hub. The approach is conceptually modeled on the way a small number of atomic bonding rules give rise to a wide range of molecular geometries — a central hub plays the role of a central atom, its ports define a "bond angle" that is itself a design variable, and each limb is built from a small set of standardized "bond modules" rather than from bespoke, non-interchangeable parts.

## 1.2 Conceptual Inspiration: The Polyatomic Analogy

The structural inspiration for this design is drawn from simple polyatomic molecules such as ammonia (NH₃), in which a single central atom (nitrogen) forms three equivalent covalent bonds to peripheral atoms (hydrogen), arranged around the center at a characteristic bond angle. In NH₃, that angle is close to — but slightly compressed from — the ideal tetrahedral angle of 109.5°, the difference being due to the geometry imposed by the central atom's electron configuration. Two features of this arrangement carry over directly to the manipulator: a single central body connects to a small number of identical peripheral chains through identical connection types, and the angle between those chains is the primary parameter that determines the overall shape of the structure.

The analogy is deliberately only partial. In a molecule, the bond angle and the bond type are fixed by the electronic structure of the atoms involved and cannot be chosen independently. In this design, the equivalent of the "bond angle" — the angle between limb ports on the central hub — is treated as a free design parameter, and the equivalent of the "bond type" — the standardized mechanical and electrical interface between the hub and each limb — is treated as a fixed specification that any limb module must satisfy. This reframing is what turns a structural analogy into a design method: rather than asking "what does the molecule look like," the question becomes "what range of structures can be built if the central connection angle is tunable and every peripheral chain plugs into the center through the same interface."

This also motivates the broader "polyatomic" framing used throughout this work. Just as a large number of distinct molecules can be built from a small number of atom types by following a common set of bonding (valence) rules, a large number of distinct manipulator configurations — parallel, serial, or hybrid — can be built from a small number of module types (the link, joint, and tooling modules introduced in the design section) by following a single shared interface rule. The hub-and-limb arrangement of a delta robot is simply the specific "molecule" that results when three identical R–L–S chains are connected to a hub at a chosen angle.

## 1.3 Advantages of the Resulting Structure

Framing the manipulator as a small set of standardized elements connected through a common interface, rather than as a bespoke assembly, produces several structural advantages that motivate the remainder of this work.

Because every limb connects to the hub through the same mechanical and electrical interface, the number of distinct part designs that must be engineered, manufactured, and stocked as spares is reduced regardless of how many limbs the final machine has or how those limbs are arranged. The same interface also means that a single limb, or a single joint within a limb, can be removed and replaced without disturbing the rest of the assembly, which directly supports field repair and hot-swapping.

Because the modules are not permanently committed to a single arrangement, the same physical hardware can be reconfigured into different kinematic "molecules" for different tasks — for example, three identical R–L–S chains arranged symmetrically around the hub for a standard delta-type configuration, or one chain rearranged into a longer serial sequence when extended reach into a confined space is needed. This reconfigurability is not available to a conventional delta robot, whose limbs are fixed, identical, and not interchangeable with any other kinematic role.

Because the hub's connection angle is treated as a tunable parameter rather than a fixed value, the overall shape of the reachable workspace — flatter and wider, or more conical and vertically biased — can be adjusted to suit the application without redesigning the limbs themselves. Finally, because failure is handled at the level of an individual module rather than the whole machine, the structure supports graceful degradation: the loss of one module can, in principle, be tolerated by reconfiguring or operating with reduced capability, rather than taking the entire manipulator out of service — the single largest practical weakness of a conventional delta robot.

## 1.4 Preliminaries: Delta Robot Architecture and Mechanical Components

Since the proposed design retains the overall topology of a delta robot for its default configuration, this section briefly establishes the baseline architecture and terminology against which the design in the following section is presented.

A standard delta robot consists of a fixed base, a moving platform, and three identical kinematic chains ("limbs") connecting the two. Each limb consists of an upper arm, driven by a motor-actuated revolute joint mounted on the base, and a forearm connecting the upper arm to the moving platform. In the conventional design, the forearm is built as a parallelogram — two parallel rigid rods, each terminating in a spherical (ball-and-socket) joint at both ends — which constrains the moving platform to remain parallel to the base at all times. This constraint is what reduces the platform's motion to pure translation (three degrees of freedom in x, y, and z) and gives the mechanism its simple, closed-form kinematics. Two terms recur throughout the design and analysis sections: the workspace, meaning the volume of points the platform can reach, and a singularity, meaning a configuration at which the relationship between actuator motion and platform motion becomes degenerate — most commonly occurring at the boundary of the workspace, where a limb is fully extended or fully folded.

At the component level, a conventional delta robot is built from a small set of mechanical elements: base-mounted actuators (typically servo motors with reduction gearing) driving the active revolute joints; rigid upper-arm and forearm links, often in lightweight materials to minimize moving mass; spherical or universal joints connecting the forearm rods to the upper arms and to the platform; the moving platform itself, which provides the mounting point for an end-effector; and the end-effector or tooling, such as a gripper or vacuum cup.

The design presented in this work retains all of these baseline elements but adds several additional components that are prerequisites for the modular and range-extending features described in the design section:

- **Hollow-shaft actuators and rotary unions**, allowing power and data cabling to pass through the active joint at the hub rather than running externally along the limb.
- **Integrated linear actuators within the forearm rods**, enabling the telescoping (variable-length) parallelogram links.
- **Double-cardan (stacked universal joint) assemblies**, used at the platform-side joint in place of a standard ball-and-socket joint to extend its usable angular range.
- **A standardized mechanical-and-electrical connector**, common to every hub port and every module-to-module interface, combining a mechanical flange and alignment features with a daisy-chained data and power connection (e.g., for a CAN or EtherCAT bus).
- **A small serial wrist module**, mounted at the center of the moving platform, providing one to three additional degrees of freedom for end-effector orientation.

These additional components are introduced in the design section as the physical embodiment of the R-, L-, S-, and W-module categories referred to throughout this work.

## 1.5 Scope of the Design

The scope of this work covers the conceptual and kinematic design of a reconfigurable, modular delta-type manipulator, and the methodology by which that design is to be developed and validated. Specifically, the work covers:

- Definition of a standardized module family (active revolute joints, telescoping links, extended-range passive joints, and an optional wrist/tooling module) sharing a common mechanical and electrical interface.
- Kinematic modeling of a baseline three-limb delta configuration and of the proposed variants, including variable hub geometry and variable-length forearms.
- Workspace and singularity analysis used to evaluate each variant against the baseline.
- A staged validation approach proceeding from parametric simulation, to single-module physical testing, to assembly and benchmarking of a full hub.

The following items are explicitly outside the scope of this work: detailed structural or finite-element analysis of individual components, control software architecture beyond the kinematic layer, manufacturing cost and supply-chain analysis, and full development of the fully spherical-jointed (3-RSS) reconfiguration mode, which is treated only as a possible future operating mode rather than a primary design target.

## 1.6 Objectives

The design work is guided by three objectives:

1. **Maximize the usable range of motion of each limb** by redesigning the active joint at the hub and the passive joint at the moving platform, so that the angular sweep available to each limb exceeds that of a standard delta forearm.

2. **Establish a modular standard** — a small set of interchangeable link and joint modules sharing a common mechanical and electrical interface — that allows the same hardware to be configured as a parallel (delta) manipulator, a serial manipulator, or a hybrid of the two, and that allows a faulty module to be replaced or bypassed without disabling the entire system.

3. **Increase the overall workspace volume relative to a standard delta of equivalent footprint**, while retaining a kinematic structure whose constraint behavior — and therefore whose singularity locations — remains predictable and well defined, so that the gains in objectives 1 and 2 do not come at the cost of unpredictable or poorly characterized motion.

## 1.7 Approach to the Design Section

The design that follows is structured to mirror the logic of these objectives rather than presenting components in an arbitrary order. It begins at the central hub, where the bond-angle parameter is defined, and proceeds outward along a single representative limb — through the active joint, the variable-length link, and the extended-range distal joint — before describing the moving platform and its optional wrist module. Each component is introduced together with the specific objective it addresses, so that the design can be read as a direct response to the scope and objectives set out above. The kinematic and workspace analysis used to evaluate this design against a standard delta baseline is presented in the section that follows the design description.
